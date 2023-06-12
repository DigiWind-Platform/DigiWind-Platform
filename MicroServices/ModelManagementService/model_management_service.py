# Author: Daniel Ramsauer <daniel.ramsauer@tuwien.ac.at>
import os
import threading
import signal
import logging
import time


from rdflib import URIRef
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import graph_helper
import triple_store_interface
from triple_store_interface import SparqlHelper
from ftp_class import FtpServer
import utils

FTP_PORT = 2121
FTP_USER = os.environ.get('FTP_USER')
FTP_PASSWORD = os.environ.get('FTP_PASSWORD')
FTP_DIRECTORY = os.sep + "app" + os.sep + "data"  # /app/data
LOG_DIRECTORY = os.sep + "app" + os.sep + "logs"  # /app/logs
SPARQL_SERVER_NAME = os.environ.get('SPARQL_SERVER_NAME')
SPARQL_SERVER_PORT = os.environ.get('SPARQL_SERVER_PORT')
SPARQL_DATASET_NAME = os.environ.get('SPARQL_DATASET_NAME')
SPARQL_USER = os.environ.get('SPARQL_USER')
SPARQL_PASSWORD = os.environ.get('SPARQL_PASSWORD')
METADATA_FILE_NAME = os.environ.get('METADATA_FILE_NAME')
FTP_PASSIVE_PORT_RANGE = os.environ.get('FTP_PASSIVE_PORT_RANGE')
ONTOLOGY_URL = os.environ.get('ONTOLOGY_URL')
ONTOLOGY_FILE_NAME = os.environ.get('ONTOLOGY_FILE_NAME')
split_ports = ''
if FTP_USER is None:
    logging.error("No FTP_USER environment variable is set")
    exit(1)
if FTP_PASSWORD is None:
    logging.error("No FTP_PASSWORD environment variable is set")
    exit(1)
if FTP_PASSIVE_PORT_RANGE is None:
    logging.error("No FTP_PASSIVE_PORT_RANGE environment variable is set")
    exit(1)
if SPARQL_SERVER_NAME is None:
    logging.error("No SPARQL_SERVER_NAME environment variable is set")
    exit(1)
if SPARQL_SERVER_PORT is None:
    logging.error("No SPARQL_SERVER_PORT environment variable is set")
    exit(1)
if SPARQL_USER is None:
    logging.error("No SPARQL_USER environment variable is set")
    exit(1)
if SPARQL_PASSWORD is None:
    logging.error("No SPARQL_PASSWORD environment variable is set")
    exit(1)
if SPARQL_DATASET_NAME is None:
    logging.error("No SPARQL_DATASET_NAME environment variable is set")
    exit(1)
if METADATA_FILE_NAME is None:
    logging.error("No METADATA_FILE_NAME environment variable is set")
    exit(1)
if ONTOLOGY_URL is None:
    logging.error("No ONTOLOGY_URL environment variable is set")
    exit(1)
if ONTOLOGY_FILE_NAME is None:
    logging.error("No ONTOLOGY_FILE_NAME environment variable is set")
    exit(1)
else:
    if '-' not in FTP_PASSIVE_PORT_RANGE:
        logging.error("FTP_PASSIVE_PORT_RANGE does not contain a range!")
        exit(1)
    split_ports = FTP_PASSIVE_PORT_RANGE.split('-')
    try:
        int(split_ports[0])
        int(split_ports[1])
    except ValueError:
        logging.error("FTP_PASSIVE_PORT_RANGE does not contain two integers as port value!")
        exit(1)

if not METADATA_FILE_NAME.endswith('.json'):
    logging.error("Defined metadata file name does not end with .json")
    exit(1)
logging_level = utils.set_log_level(os.environ.get('LOGGING_LEVEL'))
logging.root.handlers = []
logging.basicConfig(handlers=[logging.FileHandler(LOG_DIRECTORY + os.sep + "debug.log", mode='a'),
                              logging.StreamHandler()],
                    format="%(asctime)s: %(message)s",
                    level=logging_level,
                    datefmt="%H:%M:%S")

stop = False


def handle_sigterm(*args):
    global stop
    stop = True
    watcher.stop()
    ftp_server.stop()
    time.sleep(.5)
    raise KeyboardInterrupt()


class Watcher:
    def __init__(self, path):
        self.observer = Observer()
        self.path = path
        event_handler = Handler()
        self.observer.schedule(event_handler, self.path, recursive=True)

    def start(self):
        srv = threading.Thread(target=self.observer.start)
        srv.start()
        logging.info("Watcher:    : Watcher started")

    def stop(self):
        self.observer.stop()
        logging.info("Watcher:    : Watcher stopped")


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_moved(event):
        logging.debug("Watcher:    : Received moved event - from \"%s\" to \"%s\"." % (event.src_path, event.dest_path))
        if event.is_directory:
            return  # do nothing
        _dict = utils.check_for_fmu_and_info_file(ftp_server, FTP_DIRECTORY, event.dest_path, METADATA_FILE_NAME)
        if _dict is not None:
            add_fmu_to_ontology(_dict)

    @staticmethod
    def on_modified(event):
        logging.debug("Watcher:    : Received modified event - %s." % event.src_path)
        if event.is_directory:
            return  # do nothing
        _dict = utils.check_for_fmu_and_info_file(ftp_server, FTP_DIRECTORY, event.src_path, METADATA_FILE_NAME)
        if _dict is not None:
            sparql_helper.remove_fmu(_dict.get("directory"))  # TODO remove fmu entry before adding changed version
            add_fmu_to_ontology(_dict)

    @staticmethod
    def on_created(event):
        logging.debug("Watcher:    : Received created event - %s." % event.src_path)
        if event.is_directory:
            return  # do nothing
        # Take any action here when a file is first created.
        _dict = utils.check_for_fmu_and_info_file(ftp_server, FTP_DIRECTORY, event.src_path, METADATA_FILE_NAME)
        if _dict is not None:
            add_fmu_to_ontology(_dict)

    @staticmethod
    def on_deleted(event):
        logging.debug("Watcher:    : Received deleted event - %s." % event.src_path)
        # dir_name = utils.get_dir_name(get_dir_name_without_ftp_directory(FTP_DIRECTORY, event.src_path))
        dir_name = utils.get_dir_name(FTP_DIRECTORY, event.src_path)
        logging.info("Watcher:    : Deleted directory name: " + dir_name)
        try:
            if sparql_helper.get_node(dir_name):
                sparql_helper.remove_fmu(dir_name)
        except OSError:
            logging.info("Watcher:    : Lost connection to triple store. ")
            check_connection_to_triple_store()
            logging.info("Watcher:    : Restored connection to triple store. ")
            if sparql_helper.get_node(dir_name):
                sparql_helper.remove_fmu(dir_name)


def add_fmu_to_ontology(results_dict: dict):
    try:
        triple_store_interface.add_graph_to_store(generate_path_to_metadata_file(results_dict),
                                                  results_dict.get("fmu_inputs_outputs"), ontology_url, ontology_uri,
                                                  results_dict.get("fmu_file_name"), SPARQL_USER, SPARQL_PASSWORD)
    except OSError:
        logging.info("Watcher:    : Lost connection to triple store. ")
        check_connection_to_triple_store()
        logging.info("Watcher:    : Restored connection to triple store. ")
        add_fmu_to_ontology(results_dict)


def generate_graph_for_ontology(results_dict: dict):
    return graph_helper.generate_addition_graph(results_dict.get("fmu_inputs_outputs"), ontology_uri,
                                                generate_path_to_metadata_file(results_dict),
                                                results_dict.get("fmu_file_name"))


def generate_path_to_metadata_file(results_dict):
    return FTP_DIRECTORY + os.sep + results_dict.get("directory") + os.sep + METADATA_FILE_NAME


ftp_server = FtpServer(FTP_USER, FTP_PASSWORD, FTP_DIRECTORY, FTP_PORT, split_ports, logging_level)
watcher = Watcher(FTP_DIRECTORY)
sparql_helper = SparqlHelper(SPARQL_SERVER_NAME, SPARQL_SERVER_PORT, SPARQL_DATASET_NAME, logging_level)
signal.signal(signal.SIGTERM, handle_sigterm)


def check_connection_to_triple_store():
    connected = False
    while not connected:
        logging.debug(f"Main:       : connecting...")
        time.sleep(5)
        connected = sparql_helper.connected()


if __name__ == '__main__':
    try:
        logging.info(f"Main:       : ModelManagementService is starting and connecting to triple store...")
        check_connection_to_triple_store()
        logging.info(f"Main:       : ModelManagementService is connected!")
        ftp_server.start()
        watcher.start()

        # after starting, open store, check every folder, and write every node
        ontology_url = "http://" + SPARQL_SERVER_NAME + ":" + SPARQL_SERVER_PORT + "/" + SPARQL_DATASET_NAME
        ontology_uri = URIRef(ONTOLOGY_URL)
        store = triple_store_interface.open_store(ontology_url, SPARQL_USER, SPARQL_PASSWORD)
        triple_store_interface.write_graph_to_store(store, sparql_helper.init_ontology(ONTOLOGY_FILE_NAME))
        for _data_in_root in ftp_server.get_content_in_root():
            if '.' not in _data_in_root:
                _results_dict = utils.check_for_fmu_and_info_file(ftp_server, FTP_DIRECTORY,
                                                                  _data_in_root, METADATA_FILE_NAME)
                if _results_dict is None:
                    continue
                g = generate_graph_for_ontology(_results_dict)
                triple_store_interface.write_graph_to_store(store, g)
        triple_store_interface.close_store(store)
        triple_store_interface.generate_graph_ttl_file(ontology_url)

        # loop in order to catch keyboard interrupt exception
        while True:
            time.sleep(1)
    except KeyboardInterrupt as e:
        logging.info(f"Main:       : Caught keyboard interrupt. Canceling threads...")
        stop = True
        ftp_server.stop()
        watcher.stop()
