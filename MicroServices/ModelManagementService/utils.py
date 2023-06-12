import logging
import os
import re
import zipfile
from xml.dom import pulldom
import time

double_event_trigger_dict = dict()


def set_log_level(_logging_level):
    logging_level = logging.DEBUG
    if _logging_level is None:
        logging.info("Util:       : Logging set to " + str(_logging_level).upper())
    elif _logging_level.lower() == 'info':
        logging_level = logging.INFO
        logging.info("Util:       : Logging set to " + str(_logging_level).upper())
    elif _logging_level.lower() == 'debug':
        logging_level = logging.DEBUG
        logging.info("Util:       : Logging set to " + str(_logging_level).upper())
    return logging_level


def get_dir_name_without_ftp_directory(ftp_directory: str, path: str):
    if ftp_directory not in path:
        return path
    file_path = path[len(ftp_directory) + 1:]
    return file_path


def get_dir_name(ftp_directory: str, path: str):
    dir_name_without_ftp_directory_folder = get_dir_name_without_ftp_directory(ftp_directory, path)
    dir_name = dir_name_without_ftp_directory_folder.partition(os.sep)[0]
    return dir_name


def check_for_fmu_and_info_file(ftp_server, ftp_directory: str, path: str, metadata_file_name: str):
    dir_name_without_ftp_directory_folder = get_dir_name_without_ftp_directory(ftp_directory, path)
    if dir_name_without_ftp_directory_folder is None:
        return
    dir_name = get_dir_name(ftp_directory, dir_name_without_ftp_directory_folder)

    # remove old entries of double entry dict
    # if contains_double_entries(dir_name):
    #     return

    _files_in_folder = ftp_server.get_content_in_folder(dir_name)

    fmu_filter = re.compile(r"^(.*\.fmu)")
    filtered_list = list(filter(fmu_filter.match, _files_in_folder))
    if metadata_file_name not in _files_in_folder:
        logging.info("Watcher:    : " + metadata_file_name + " " + ("" if filtered_list else "and FMU file *.fmu ")
                     + "is missing in folder " + dir_name)
        return
    if not filtered_list:
        logging.info("Watcher:    : FMU file *.fmu is missing in folder " + dir_name)
        return
    if len(filtered_list) > 1:
        logging.info("Watcher:    : There are too many *.fmu files within the folder " +
                     dir_name + ": " + str(filtered_list))
        return

    # check if directory name is the same as the *.fmu file
    # if dir_name != filtered_list[0].partition('.')[0]:
    #     logging.info("Watcher:    : Directory name \"" + dir_name + "\" and FMU file \"" + filtered_list[0]
    #                  + "\" do not have the same name")
    #     return

    logging.info("Watcher:    : " + metadata_file_name + " and " + filtered_list[0] + " exist in folder: " + dir_name)
    path_to_fmu_with_fmu_name = dir_name + os.sep + filtered_list[0]
    results_fmu = read_fmu_standard_2_0(ftp_directory, path_to_fmu_with_fmu_name)

    return {"directory": dir_name, "fmu_inputs_outputs": results_fmu, "fmu_file_name": path_to_fmu_with_fmu_name}


# def contains_double_entries(dir_name):
#     now = time.time()
#     to_remove_paths = []
#     for key, value in double_event_trigger_dict.items():
#         if (int(now - value)) > 8:
#             to_remove_paths.append(key)
#     for p in to_remove_paths:
#         double_event_trigger_dict.pop(p)
#     # check for double event call modified and moved/created
#     if dir_name not in double_event_trigger_dict:
#         double_event_trigger_dict[dir_name] = now
#     else:
#         if int(now - double_event_trigger_dict[dir_name]) < 8:
#             return True
#     return False


def read_fmu_standard_2_0(ftp_directory: str, path_to_fmu_with_fmu_name: str):
    try:
        with zipfile.ZipFile(ftp_directory + os.sep + path_to_fmu_with_fmu_name, 'r') as zp:
            description = zp.open('modelDescription.xml')
            doc = pulldom.parse(description)
            results = dict()
            results["input"] = list()
            results["output"] = list()
            for event, node in doc:
                if event == pulldom.START_ELEMENT and node.tagName == 'ScalarVariable':
                    if node.getAttribute('causality') == "input":
                        logging.debug("Watcher:    : Input of " + path_to_fmu_with_fmu_name +
                                      " is " + node.getAttribute('name'))
                        results.get("input").append(node.getAttribute('name'))
                    if node.getAttribute('causality') == "output":
                        logging.debug("Watcher:    : Output of " + path_to_fmu_with_fmu_name +
                                      " is " + node.getAttribute('name'))
                        results.get("output").append(node.getAttribute('name'))
            return results
    except zipfile.BadZipFile:
        logging.error("Watcher:    : File " + path_to_fmu_with_fmu_name + " is not a zip file!")
