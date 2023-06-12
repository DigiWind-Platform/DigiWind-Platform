
import wx.stc


class TextWidget(wx.stc.StyledTextCtrl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.SetLexer(wx.stc.STC_LEX_JSON)
        # self.StyleClearAll()
        self.SetLexer(wx.stc.STC_LEX_JSON)

        self.SetKeyWords(0, 'mandatory')

        self.StyleSetSpec(wx.stc.STC_JSON_KEYWORD, 'fore:red, bold')

        self.StyleSetSpec(wx.stc.STC_JSON_DEFAULT, 'fore:black')
        self.StyleSetSpec(wx.stc.STC_JSON_STRING, 'fore:black')
        self.StyleSetSpec(wx.stc.STC_JSON_NUMBER, 'fore:purple')

        self.StyleSetSpec(wx.stc.STC_JSON_PROPERTYNAME, 'fore:blue, italic')
        self.StyleSetSpec(wx.stc.STC_JSON_ESCAPESEQUENCE, 'fore:blue, bold')
        self.StyleSetSpec(wx.stc.STC_JSON_LINECOMMENT, 'fore:green, italic')
        self.StyleSetSpec(wx.stc.STC_JSON_BLOCKCOMMENT, 'fore:green, italic')
        self.StyleSetSpec(wx.stc.STC_JSON_OPERATOR, 'fore:blue, bold')
        self.StyleSetSpec(wx.stc.STC_JSON_URI, 'fore:purple, underline')
        self.StyleSetSpec(wx.stc.STC_JSON_COMPACTIRI, 'fore:blue, bold')
        self.StyleSetSpec(wx.stc.STC_JSON_LDKEYWORD, 'fore:blue, bold')
        self.StyleSetSpec(wx.stc.STC_JSON_ERROR, 'fore:red, bold')
