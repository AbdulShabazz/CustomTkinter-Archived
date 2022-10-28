import tkinter
import sys
from typing import Union, Tuple, Callable

from .core_rendering.ctk_canvas import CTkCanvas
from ..theme_manager import ThemeManager
from .core_rendering.draw_engine import DrawEngine
from .core_widget_classes.widget_base_class import CTkBaseClass
from .font.ctk_font import CTkFont


class CTkRadioButton(CTkBaseClass):
    """
    Radiobutton with rounded corners, border, label, variable support, command.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: any = None,
                 width: int = 100,
                 height: int = 22,
                 radiobutton_width: int = 22,
                 radiobutton_height: int = 22,
                 corner_radius: Union[int, str] = "default_theme",
                 border_width_unchecked: Union[int, str] = "default_theme",
                 border_width_checked: Union[int, str] = "default_theme",

                 bg_color: Union[str, Tuple[str, str], None] = None,
                 fg_color: Union[str, Tuple[str, str]] = "default_theme",
                 hover_color: Union[str, Tuple[str, str]] = "default_theme",
                 border_color: Union[str, Tuple[str, str]] = "default_theme",
                 text_color: Union[str, Tuple[str, str]] = "default_theme",
                 text_color_disabled: Union[str, Tuple[str, str]] = "default_theme",

                 text: str = "CTkRadioButton",
                 font: Union[tuple, CTkFont] = "default_theme",
                 textvariable: tkinter.Variable = None,
                 variable: tkinter.Variable = None,
                 value: Union[int, str] = 0,
                 state: str = tkinter.NORMAL,
                 hover: bool = True,
                 command: Callable = None,
                 **kwargs):

        # transfer basic functionality (_bg_color, size, _appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # dimensions
        self._radiobutton_width = radiobutton_width
        self._radiobutton_height = radiobutton_height

        # color
        self._fg_color = ThemeManager.theme["color"]["button"] if fg_color == "default_theme" else fg_color
        self._hover_color = ThemeManager.theme["color"]["button_hover"] if hover_color == "default_theme" else hover_color
        self._border_color = ThemeManager.theme["color"]["checkbox_border"] if border_color == "default_theme" else border_color

        # shape
        self._corner_radius = ThemeManager.theme["shape"]["radiobutton_corner_radius"] if corner_radius == "default_theme" else corner_radius
        self._border_width_unchecked = ThemeManager.theme["shape"]["radiobutton_border_width_unchecked"] if border_width_unchecked == "default_theme" else border_width_unchecked
        self._border_width_checked = ThemeManager.theme["shape"]["radiobutton_border_width_checked"] if border_width_checked == "default_theme" else border_width_checked
        self._border_width = self._border_width_unchecked

        # text
        self._text = text
        self._text_label: Union[tkinter.Label, None] = None
        self._text_color = ThemeManager.theme["color"]["text"] if text_color == "default_theme" else text_color
        self._text_color_disabled = ThemeManager.theme["color"]["text_disabled"] if text_color_disabled == "default_theme" else text_color_disabled

        # font
        self._font = CTkFont() if font == "default_theme" else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # callback and control variables
        self._command = command
        self._state = state
        self._hover = hover
        self._check_state: bool = False
        self._value = value
        self._variable: tkinter.Variable = variable
        self._variable_callback_blocked: bool = False
        self._textvariable = textvariable
        self._variable_callback_name: Union[str, None] = None

        # configure grid system (3x1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0, minsize=self._apply_widget_scaling(6))
        self.grid_columnconfigure(2, weight=1)

        self._bg_canvas = CTkCanvas(master=self,
                                    highlightthickness=0,
                                    width=self._apply_widget_scaling(self._current_width),
                                    height=self._apply_widget_scaling(self._current_height))
        self._bg_canvas.grid(row=0, column=0, columnspan=3, sticky="nswe")

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._radiobutton_width),
                                 height=self._apply_widget_scaling(self._radiobutton_height))
        self._canvas.grid(row=0, column=0)
        self._draw_engine = DrawEngine(self._canvas)

        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)
        self._canvas.bind("<Button-1>", self.invoke)

        self._text_label = tkinter.Label(master=self,
                                         bd=0,
                                         padx=0,
                                         pady=0,
                                         text=self._text,
                                         justify=tkinter.LEFT,
                                         font=self._apply_font_scaling(self._font),
                                         textvariable=self._textvariable)
        self._text_label.grid(row=0, column=2, sticky="w")
        self._text_label["anchor"] = "w"

        self._text_label.bind("<Enter>", self._on_enter)
        self._text_label.bind("<Leave>", self._on_leave)
        self._text_label.bind("<Button-1>", self.invoke)

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._check_state = True if self._variable.get() == self._value else False

        self._draw()  # initial draw
        self._set_cursor()

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self.grid_columnconfigure(1, weight=0, minsize=self._apply_widget_scaling(6))
        self._text_label.configure(font=self._apply_font_scaling(self._font))

        self._bg_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                  height=self._apply_widget_scaling(self._desired_height))
        self._canvas.configure(width=self._apply_widget_scaling(self._radiobutton_width),
                               height=self._apply_widget_scaling(self._radiobutton_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int = None, height: int = None):
        super()._set_dimensions(width, height)

        self._bg_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                  height=self._apply_widget_scaling(self._desired_height))

    def _update_font(self):
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._text_label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._bg_canvas.grid_forget()
        self._bg_canvas.grid(row=0, column=0, columnspan=3, sticky="nswe")

    def destroy(self):
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        super().destroy()

    def _draw(self, no_color_updates=False):
        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._radiobutton_width),
                                                                              self._apply_widget_scaling(self._radiobutton_height),
                                                                              self._apply_widget_scaling(self._corner_radius),
                                                                              self._apply_widget_scaling(self._border_width))

        if no_color_updates is False or requires_recoloring:
            self._bg_canvas.configure(bg=ThemeManager.single_color(self._bg_color, self._appearance_mode))
            self._canvas.configure(bg=ThemeManager.single_color(self._bg_color, self._appearance_mode))

            if self._check_state is False:
                self._canvas.itemconfig("border_parts",
                                        outline=ThemeManager.single_color(self._border_color, self._appearance_mode),
                                        fill=ThemeManager.single_color(self._border_color, self._appearance_mode))
            else:
                self._canvas.itemconfig("border_parts",
                                        outline=ThemeManager.single_color(self._fg_color, self._appearance_mode),
                                        fill=ThemeManager.single_color(self._fg_color, self._appearance_mode))

            self._canvas.itemconfig("inner_parts",
                                    outline=ThemeManager.single_color(self._bg_color, self._appearance_mode),
                                    fill=ThemeManager.single_color(self._bg_color, self._appearance_mode))

            if self._state == tkinter.DISABLED:
                self._text_label.configure(fg=ThemeManager.single_color(self._text_color_disabled, self._appearance_mode))
            else:
                self._text_label.configure(fg=ThemeManager.single_color(self._text_color, self._appearance_mode))

            self._text_label.configure(bg=ThemeManager.single_color(self._bg_color, self._appearance_mode))

    def configure(self, require_redraw=False, **kwargs):
        if "radiobutton_width" in kwargs:
            self._radiobutton_width = kwargs.pop("radiobutton_width")
            self._canvas.configure(width=self._apply_widget_scaling(self._radiobutton_width))
            require_redraw = True

        if "radiobutton_height" in kwargs:
            self._radiobutton_height = kwargs.pop("radiobutton_height")
            self._canvas.configure(height=self._apply_widget_scaling(self._radiobutton_height))
            require_redraw = True

        if "text" in kwargs:
            self._text = kwargs.pop("text")
            self._text_label.configure(text=self._text)

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)

            self._update_font()

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True

        if "hover_color" in kwargs:
            self._hover_color = kwargs.pop("hover_color")
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True

        if "hover" in kwargs:
            self._hover = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            self._text_label.configure(textvariable=self._textvariable)

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)

            self._variable = kwargs.pop("variable")

            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self._check_state = True if self._variable.get() == self._value else False
                require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width_unchecked":
            return self._border_width_unchecked
        elif attribute_name == "border_width_checked":
            return self._border_width_checked
        elif attribute_name == "radiobutton_width":
            return self._radiobutton_width
        elif attribute_name == "radiobutton_height":
            return self._radiobutton_height

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text_color_disabled":
            return self._text_color_disabled

        elif attribute_name == "text":
            return self._text
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "value":
            return self._value
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "hover":
            return self._hover
        elif attribute_name == "command":
            return self._command

        else:
            return super().cget(attribute_name)

    def _set_cursor(self):
        if self._cursor_manipulation_enabled:
            if self._state == tkinter.DISABLED:
                if sys.platform == "darwin":
                    self._canvas.configure(cursor="arrow")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="arrow")
                elif sys.platform.startswith("win"):
                    self._canvas.configure(cursor="arrow")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="arrow")

            elif self._state == tkinter.NORMAL:
                if sys.platform == "darwin":
                    self._canvas.configure(cursor="pointinghand")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="pointinghand")
                elif sys.platform.startswith("win"):
                    self._canvas.configure(cursor="hand2")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="hand2")

    def _on_enter(self, event=0):
        if self._hover is True and self._state == tkinter.NORMAL:
            self._canvas.itemconfig("border_parts",
                                    fill=ThemeManager.single_color(self._hover_color, self._appearance_mode),
                                    outline=ThemeManager.single_color(self._hover_color, self._appearance_mode))

    def _on_leave(self, event=0):
        if self._check_state is True:
            self._canvas.itemconfig("border_parts",
                                    fill=ThemeManager.single_color(self._fg_color, self._appearance_mode),
                                    outline=ThemeManager.single_color(self._fg_color, self._appearance_mode))
        else:
            self._canvas.itemconfig("border_parts",
                                    fill=ThemeManager.single_color(self._border_color, self._appearance_mode),
                                    outline=ThemeManager.single_color(self._border_color, self._appearance_mode))

    def _variable_callback(self, var_name, index, mode):
        if not self._variable_callback_blocked:
            if self._variable.get() == self._value:
                self.select(from_variable_callback=True)
            else:
                self.deselect(from_variable_callback=True)

    def invoke(self, event=0):
        if self._state == tkinter.NORMAL:
            if self._check_state is False:
                self._check_state = True
                self.select()

        if self._command is not None:
            self._command()

    def select(self, from_variable_callback=False):
        self._check_state = True
        self._border_width = self._border_width_checked
        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(self._value)
            self._variable_callback_blocked = False

    def deselect(self, from_variable_callback=False):
        self._check_state = False
        self._border_width = self._border_width_unchecked
        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set("")
            self._variable_callback_blocked = False

    def bind(self, sequence=None, command=None, add=None):
        """ called on the tkinter.Canvas """
        return self._canvas.bind(sequence, command, add)

    def unbind(self, sequence, funcid=None):
        """ called on the tkinter.Canvas """
        return self._canvas.unbind(sequence, funcid)

    def focus(self):
        return self._text_label.focus()

    def focus_set(self):
        return self._text_label.focus_set()

    def focus_force(self):
        return self._text_label.focus_force()
