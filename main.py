# --- main.py (Final, Complete Version) ---

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.textinput import TextInput
from kivy.uix.splitter import Splitter
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
import os
import subprocess
import json

try:
    import git
except ImportError:
    git = None

# THE DEFINITIVE FIX: Import our own widget from our own file
from code_widget import CodeInput

kivy.require('2.0.0')

CONFIG_FILE = 'config.json'
THEMES = {
    'dark': { 'bg': get_color_from_hex('#1e1e1e'), 'fg': get_color_from_hex('#d4d4d4'), 'input_bg': get_color_from_hex('#252526'), 'button_bg': get_color_from_hex('#333333'), 'splitter_bg': get_color_from_hex('#3c3c3c'), 'code_style': 'monokai' },
    'light': { 'bg': get_color_from_hex('#ffffff'), 'fg': get_color_from_hex('#000000'), 'input_bg': get_color_from_hex('#f0f0f0'), 'button_bg': get_color_from_hex('#e0e0e0'), 'splitter_bg': get_color_from_hex('#cccccc'), 'code_style': 'default' }
}

class GitPopup(Popup):
    def __init__(self, repo_path, theme, **kwargs):
        super().__init__(**kwargs)
        self.title = "Git Version Control"; self.size_hint = (0.9, 0.9); self.repo_path = repo_path; self.repo = None
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        self.output_console = TextInput(readonly=True, size_hint_y=0.6, background_color=THEMES[theme]['input_bg'], foreground_color=THEMES[theme]['fg'])
        try:
            if git: self.repo = git.Repo(self.repo_path); self.output_console.text = "Git repository loaded."
            else: self.output_console.text = "GitPython library not found."
        except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError) if git else Exception: self.repo = None; self.output_console.text = "Not a Git repository. You can initialize one."
        button_grid = BoxLayout(size_hint_y=0.4, spacing=5)
        init_button = Button(text="Init", on_press=self.git_init); status_button = Button(text="Status", on_press=self.git_status)
        self.commit_input = TextInput(hint_text="Commit message...", size_hint_y=None, height=40, background_color=THEMES[theme]['input_bg'], foreground_color=THEMES[theme]['fg'])
        commit_button = Button(text="Commit All", on_press=self.git_commit_all, size_hint_y=None, height=40)
        pull_button = Button(text="Pull", on_press=self.git_pull); push_button = Button(text="Push", on_press=self.git_push)
        commit_layout = BoxLayout(orientation='vertical'); commit_layout.add_widget(self.commit_input); commit_layout.add_widget(commit_button)
        button_grid.add_widget(init_button); button_grid.add_widget(status_button); button_grid.add_widget(commit_layout); button_grid.add_widget(pull_button); button_grid.add_widget(push_button)
        layout.add_widget(button_grid); layout.add_widget(Label(text="Output:", color=THEMES[theme]['fg'])); layout.add_widget(self.output_console)
        self.content = layout
    def git_init(self, instance):
        try: self.repo = git.Repo.init(self.repo_path); self.output_console.text = f"Initialized empty Git repository."
        except Exception as e: self.output_console.text = f"Error: {e}"
    def git_status(self, instance):
        if self.repo: self.output_console.text = self.repo.git.status()
    def git_pull(self, instance):
        if self.repo: self.output_console.text = self.repo.git.pull()
    def git_push(self, instance):
        if self.repo: self.output_console.text = self.repo.git.push()
    def git_commit_all(self, instance):
        if not self.repo: self.output_console.text = "Error: Not a Git repository."; return
        commit_message = self.commit_input.text.strip()
        if not commit_message: self.output_console.text = "Error: Commit message cannot be empty."; return
        try:
            self.output_console.text = "Running 'git add .'..."
            self.repo.git.add(A=True)
            self.output_console.text += f"\nRunning 'git commit'..."
            commit_output = self.repo.git.commit(m=commit_message)
            self.output_console.text = f"--- COMMIT SUCCESS ---\n{commit_output}"; self.commit_input.text = ""
        except git.exc.GitCommandError as e: self.output_console.text = f"Git Error:\n{e.stderr}"

class PipPopup(Popup):
    def __init__(self, theme, **kwargs):
        super().__init__(**kwargs)
        self.title = "Pip Package Manager"; self.size_hint = (0.9, 0.9)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        self.output_console = TextInput(readonly=True, size_hint_y=0.7, background_color=THEMES[theme]['input_bg'], foreground_color=THEMES[theme]['fg'])
        self.package_input = TextInput(hint_text="Enter library name (e.g., requests)", size_hint_y=None, height=44, multiline=False, background_color=THEMES[theme]['input_bg'], foreground_color=THEMES[theme]['fg'])
        button_grid = BoxLayout(size_hint_y=None, height=44, spacing=5)
        install_button = Button(text="Install", on_press=self.run_pip_install); uninstall_button = Button(text="Uninstall", on_press=self.run_pip_uninstall); upgrade_button = Button(text="Upgrade", on_press=self.run_pip_upgrade)
        button_grid.add_widget(install_button); button_grid.add_widget(uninstall_button); button_grid.add_widget(upgrade_button)
        layout.add_widget(self.package_input); layout.add_widget(button_grid); layout.add_widget(Label(text="Output Console:", size_hint_y=None, height=20, color=THEMES[theme]['fg'])); layout.add_widget(self.output_console)
        self.content = layout
    def run_pip_command(self, command):
        package_name = self.package_input.text.strip()
        if not package_name: self.output_console.text = "Error: Please enter a package name."; return
        self.output_console.text = f"Running 'pip {command} {package_name}'...\nPlease wait..."
        Clock.schedule_once(lambda dt: self._execute_command(command, package_name), 0.1)
    def _execute_command(self, command, package_name):
        try:
            full_command = ['python', '-m', 'pip'] + command.split() + [package_name]
            if command == 'uninstall': full_command.append('-y')
            result = subprocess.run(full_command, capture_output=True, text=True, timeout=300)
            self.output_console.text = f"--- OUTPUT ---\n{result.stdout}\n--- ERRORS ---\n{result.stderr}"
        except Exception as e: self.output_console.text = f"An error occurred: {str(e)}"
    def run_pip_install(self, instance): self.run_pip_command('install')
    def run_pip_uninstall(self, instance): self.run_pip_command('uninstall')
    def run_pip_upgrade(self, instance): self.run_pip_command('install --upgrade')

class CodeTab(TabbedPanelItem):
    def __init__(self, filepath, theme, **kwargs):
        super().__init__(**kwargs)
        self.filepath = filepath
        self.text = os.path.basename(filepath)
        self.editor = CodeInput(
            theme=THEMES[theme]['code_style'],
            font_name='monospace',
            font_size='14sp',
            background_color=THEMES[theme]['input_bg'],
            foreground_color=THEMES[theme]['fg']
        )
        self.content = self.editor

class CodeEditorApp(App):
    title = "Code Editor"
    
    def build(self):
        self.current_theme = 'dark'; self.project_path = None
        self.root_layout = BoxLayout(orientation='horizontal')
        self.splitter = Splitter(sizable_from='right')
        self.file_browser_layout = BoxLayout(orientation='vertical')
        self.path_label = Label(text="No Folder Selected", size_hint_y=0.05)
        self.file_browser_layout.add_widget(self.path_label)
        self.tree_view = TreeView(hide_root=True, size_hint_y=0.95); self.tree_view.bind(on_node_touch_down=self.on_file_node_touch)
        scroll_view = ScrollView(); scroll_view.add_widget(self.tree_view); self.file_browser_layout.add_widget(scroll_view)
        self.splitter.add_widget(self.file_browser_layout)
        self.editor_panel = BoxLayout(orientation='vertical')
        self.top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        self.tab_panel = TabbedPanel(do_default_tab=False)
        self.editor_panel.add_widget(self.top_bar); self.editor_panel.add_widget(self.tab_panel)
        self.splitter.add_widget(self.editor_panel); self.root_layout.add_widget(self.splitter)
        self.apply_theme(); Clock.schedule_once(self.post_build_init, 0)
        return self.root_layout
    def post_build_init(self, dt):
        self.load_config()
        if not self.project_path or not os.path.isdir(self.project_path): self.show_path_selection_popup()
        else: self.refresh_file_browser()
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f: self.project_path = json.load(f).get('project_path')
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f: json.dump({'project_path': self.project_path}, f)
    def show_path_selection_popup(self, instance=None):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text="Enter the full path to your project folder."))
        self.path_input = TextInput(text=self.project_path or "", hint_text="/storage/emulated/0/Documents/MyProject")
        content.add_widget(self.path_input)
        ok_button = Button(text="Set Project Folder", size_hint_y=None, height=44)
        content.add_widget(ok_button)
        popup = Popup(title="Select Project Folder", content=content, size_hint=(0.9, 0.6), auto_dismiss=False)
        ok_button.bind(on_press=lambda x: self.set_project_path(self.path_input.text, popup)); popup.open()
    def set_project_path(self, path, popup):
        if path and os.path.isdir(path):
            self.project_path = path; self.save_config(); self.path_label.text = os.path.basename(path)
            self.tab_panel.clear_tabs(); self.refresh_file_browser(); popup.dismiss()
        else: self.show_info_popup("Error", f"Not a valid directory:\n{path}")
    def refresh_file_browser(self):
        self.tree_view.clear_widgets()
        if self.project_path: self.populate_file_tree(self.project_path, None)
    def populate_file_tree(self, path, parent_node):
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            node = self.tree_view.add_node(TreeViewLabel(text=item), parent_node)
            if os.path.isdir(item_path): node.is_open = False; self.populate_file_tree(item_path, node)
            else: node.filepath = item_path
    def on_file_node_touch(self, instance, node):
        if hasattr(node, 'filepath'): self.load_file(node.filepath)
    def apply_theme(self):
        theme = THEMES[self.current_theme]; self.root_layout.canvas.before.clear()
        with self.root_layout.canvas.before: Color(*theme['bg']); Rectangle(pos=self.root_layout.pos, size=self.root_layout.size)
        self.top_bar.clear_widgets()
        buttons_data = [('New', self.new_file), ('Save', self.save_file), ('Run', self.run_code), ('Change Folder', self.show_path_selection_popup)]
        if git: buttons_data.append(('Git', self.open_git_popup))
        buttons_data.extend([('Pip', self.open_pip_popup), ('Toggle Theme', self.toggle_theme)])
        for text, func in buttons_data:
            btn = Button(text=text, on_press=func, background_color=theme['button_bg'], color=theme['fg'])
            self.top_bar.add_widget(btn)
        for tab in self.tab_panel.tab_list:
            tab.editor.background_color = theme['input_bg']
            tab.editor.foreground_color = theme['fg']
    def toggle_theme(self, instance):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'; self.apply_theme()
    def get_current_tab_or_show_error(self):
        if not self.project_path: self.show_info_popup("Error", "Set a project folder first."); return None
        current_tab = self.tab_panel.current_tab
        if not current_tab: self.show_info_popup("Error", "No active file selected."); return None
        return current_tab
    def new_file(self, instance=None):
        if not self.project_path: self.show_info_popup("Error", "Please set a project folder first."); return
        i = 1
        while True: filepath = os.path.join(self.project_path, f"untitled-{i}.py");
            if not os.path.exists(filepath): break; i += 1
        new_tab = CodeTab(filepath=filepath, theme=self.current_theme); self.tab_panel.add_widget(new_tab); self.tab_panel.switch_to(new_tab)
    def load_file(self, filepath):
        if not os.path.exists(filepath): self.show_info_popup("Error", f"File not found: {filepath}"); return
        for tab in self.tab_panel.tab_list:
            if tab.filepath == filepath: self.tab_panel.switch_to(tab); return
        new_tab = CodeTab(filepath=filepath, theme=self.current_theme)
        with open(filepath, 'r') as f: new_tab.editor.text = f.read()
        self.tab_panel.add_widget(new_tab); self.tab_panel.switch_to(new_tab)
    def save_file(self, instance=None):
        current_tab = self.get_current_tab_or_show_error()
        if not current_tab: return False
        try:
            with open(current_tab.filepath, 'w') as f: f.write(current_tab.editor.text)
            self.show_info_popup("Success", f"Saved {current_tab.filepath}"); return True
        except Exception as e: self.show_info_popup("Error", f"Could not save file:\n{e}"); return False
    def run_code(self, instance=None):
        current_tab = self.get_current_tab_or_show_error()
        if not current_tab: return
        if self.save_file():
            try:
                result = subprocess.run(['python', current_tab.filepath], capture_output=True, text=True, timeout=10)
                self.show_info_popup("Execution Output", f"--- OUTPUT ---\n{result.stdout}\n--- ERRORS ---\n{result.stderr}", font='monospace')
            except Exception as e: self.show_info_popup("Execution Error", str(e))
    def open_git_popup(self, instance):
        if not self.project_path: self.show_info_popup("Error", "Set a project folder first."); return
        GitPopup(repo_path=self.project_path, theme=self.current_theme).open()
    def show_info_popup(self, title, content_text, font='sans'):
        theme = THEMES[self.current_theme]
        content = ScrollView(); popup_label = Label(text=content_text, size_hint_y=None, font_name=font, halign='left', valign='top', color=theme['fg'])
        popup_label.bind(texture_size=popup_label.setter('size')); content.add_widget(popup_label)
        Popup(title=title, content=content, size_hint=(0.9, 0.9), background_color=theme['bg']).open()

if __name__ == '__main__':
    CodeEditorApp().run()
