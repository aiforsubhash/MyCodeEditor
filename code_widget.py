# --- code_widget.py ---

from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatter import Formatter
from kivy.utils import get_color_from_hex

# This is a custom formatter to convert Pygments' HTML styles to Kivy's [color] tags
class KivyFormatter(Formatter):
    def __init__(self, **kwargs):
        super(KivyFormatter, self).__init__(**kwargs)
        self.kivy_styles = {}
        # Simple default styles
        self.kivy_styles['Token.Keyword'] = '[color=0000ff]'
        self.kivy_styles['Token.Name'] = '[color=000000]'
        self.kivy_styles['Token.String'] = '[color=008000]'
        self.kivy_styles['Token.Operator'] = '[color=ff0000]'
        self.kivy_styles['Token.Comment'] = '[color=808080]'
        self.kivy_styles['Token.Number'] = '[color=008080]'
        
        # Load styles from the pygments style
        for token, style in self.style:
            color = style['color']
            if color:
                self.kivy_styles[str(token)] = f"[color={color}]"

    def format(self, tokensource, outfile):
        text_parts = []
        for ttype, tvalue in tokensource:
            # Replace special characters that conflict with Kivy markup
            tvalue = tvalue.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            style_tag_open = self.kivy_styles.get(str(ttype), None)
            if style_tag_open:
                # Close the color tag for this token
                text_parts.append(f"{style_tag_open}{tvalue}[/color]")
            else:
                text_parts.append(tvalue)
        outfile.write("".join(text_parts))

class CodeInput(TextInput):
    theme = StringProperty('default')

    def __init__(self, **kwargs):
        super(CodeInput, self).__init__(**kwargs)
        self.multiline = True
        self.markup = True  # MUST be true to allow [color] tags
        self.font_name = 'monospace'
        self._highlight_schedule = None

        # Bind a function to be called when text changes
        self.bind(text=self.schedule_highlighting)

    def schedule_highlighting(self, *args):
        # This is a performance optimization. Instead of highlighting on every
        # single keystroke, we wait a fraction of a second. If the user is still
        # typing, we cancel and reschedule. This prevents lag.
        if self._highlight_schedule:
            self._highlight_schedule.cancel()
        self._highlight_schedule = Clock.schedule_once(self.highlight_text, 0.1)

    def highlight_text(self, *args):
        # Get current text and cursor position
        original_text = self.text
        cursor_pos = self.cursor
        
        # Temporarily disable the binding to prevent a recursive loop
        self.unbind(text=self.schedule_highlighting)
        
        try:
            # This is the core of the syntax highlighting
            highlighted_text = highlight(original_text, PythonLexer(), KivyFormatter(style=self.theme))
            self.text = highlighted_text
        except Exception:
            # If highlighting fails, just revert to the original text
            self.text = original_text
        
        # Restore the cursor to its original position
        self.cursor = cursor_pos
        
        # Re-enable the binding
        self.bind(text=self.schedule_highlighting)
