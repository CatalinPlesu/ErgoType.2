"""
Rich-based interactive menu system for ErgoType.2
Provides a nicer user interface with colors, tables, and panels.
"""

import sys
import logging
from typing import List, Callable, Optional, Any, Dict, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.text import Text
from rich import box
from rich.layout import Layout
from rich.live import Live
from pathlib import Path

# Import preferences at module level for efficiency
try:
    from ui.preferences import Preferences
    PREFERENCES_AVAILABLE = True
except ImportError:
    PREFERENCES_AVAILABLE = False


# Create a module-level console for convenience functions
# Individual classes and functions can create their own instances if needed
_console = Console()


def get_console() -> Console:
    """Get the module-level console instance"""
    return _console


# Export console for backward compatibility
console = _console


class RichMenu:
    """Interactive menu using Rich library for better UI with keyboard navigation"""
    
    def __init__(self, title: str = "Menu", use_preferences: bool = True):
        self.title = title
        self.items: List[Tuple[str, Callable]] = []
        self.selected = 1  # Default to option 1
        self.use_preferences = use_preferences and PREFERENCES_AVAILABLE
        
        # Load last selection if preferences enabled
        if self.use_preferences:
            try:
                prefs = Preferences()
                self.selected = prefs.get_last_menu_selection()
            except (IOError, ValueError, KeyError):
                # If preferences can't be loaded, default to option 1
                self.selected = 1
    
    def add_item(self, title: str, func: Callable) -> None:
        """Add a menu item with title and callback function"""
        self.items.append((title, func))
    
    def _get_key(self) -> Optional[str]:
        """Get a single keypress from user (similar to old menu)"""
        import tty
        import termios
        
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        
        try:
            tty.setraw(fd)
            k = sys.stdin.read(1)
            
            if not k:
                return None
            
            if ord(k) in (10, 13):   # Enter
                return "enter"
            if ord(k) == 3:          # Ctrl+C
                raise KeyboardInterrupt
            if ord(k) == 9:          # Tab
                return "down"
            if ord(k) == 27:         # escape or arrow
                k2 = sys.stdin.read(1)
                if k2 == '[':
                    k3 = sys.stdin.read(1)
                    return {
                        'A': 'up',
                        'B': 'down',
                        'C': 'right',
                        'D': 'left'
                    }.get(k3, None)
                return "escape"
            
            if k.isdigit():
                return k
            
            return k.lower()
        
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    
    def _draw(self) -> None:
        """Draw the menu with current selection highlighted"""
        console.clear()
        
        # Create menu table
        table = Table(
            title=f"[bold cyan]{self.title}[/bold cyan]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("#", style="cyan", justify="right", width=4)
        table.add_column("Option", style="white")
        
        # Add menu items with highlight for selected
        menu_len = len(self.items) + 1  # +1 for Exit option
        for idx in range(menu_len):
            if idx == 0:
                label = "[red]Exit[/red]"
                num = "0"
            else:
                label = self.items[idx - 1][0]
                num = str(idx)
            
            # Highlight selected item
            if idx == self.selected:
                table.add_row(f"[bold green]{num}[/bold green]", f"[bold green]→ {label}[/bold green]")
            else:
                table.add_row(num, label)
        
        console.print(table)
        console.print()
        console.print("[dim]Use arrows/vim keys (↑↓jk) or numbers. Enter to select. Esc to exit.[/dim]")
        console.print()
    
    def display(self) -> None:
        """Display the menu and get user selection with keyboard navigation"""
        running = True
        
        while running:
            try:
                self._draw()
                key = self._get_key()
                
                if key in ("up", "k"):
                    # Move selection up
                    self.selected = (self.selected - 1) % (len(self.items) + 1)
                
                elif key in ("down", "j", "tab"):
                    # Move selection down
                    self.selected = (self.selected + 1) % (len(self.items) + 1)
                
                elif key in ("escape", "left", "h"):
                    # Exit
                    running = False
                
                elif key == "enter":
                    # Execute selected item
                    console.clear()
                    
                    if self.selected == 0:
                        # Exit selected
                        console.print("[yellow]Exiting...[/yellow]")
                        running = False
                    else:
                        # Save selection if not Exit (0)
                        if self.use_preferences:
                            try:
                                prefs = Preferences()
                                prefs.set_last_menu_selection(self.selected)
                                prefs.save()
                            except (IOError, OSError) as e:
                                # If preferences can't be saved, continue without error
                                # (menu functionality should not be blocked by preference saving)
                                logging.debug(f"Could not save menu selection preference: {e}")
                        
                        # Execute menu item function
                        _, func = self.items[self.selected - 1]
                        try:
                            func()
                        except KeyboardInterrupt:
                            console.print("\n[yellow]Operation cancelled[/yellow]")
                        except Exception as e:
                            console.print(f"[red]Error: {e}[/red]")
                            console.print_exception()
                        
                        console.print()
                        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                
                elif key and key.isdigit():
                    # Direct number selection
                    num = int(key)
                    if 0 <= num <= len(self.items):
                        self.selected = num
            
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Interrupted. Exiting...[/yellow]")
                running = False


def select_from_list(
    title: str,
    items: List[Tuple[str, Any]],
    default_value: Optional[Any] = None,
    show_size: bool = False
) -> Optional[Tuple[int, Any]]:
    """
    Display a selection menu for a list of items.
    
    Args:
        title: Title for the selection
        items: List of (name, value) or (name, value, size) tuples
        default_value: Default value to pre-select
        show_size: Whether to show size column (for file sizes)
    
    Returns:
        Tuple of (index, value) or None if cancelled
    """
    # Create table
    table = Table(
        title=f"[bold cyan]{title}[/bold cyan]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    table.add_column("#", style="cyan", justify="right", width=4)
    table.add_column("Name", style="white")
    if show_size:
        table.add_column("Size", style="yellow", justify="right")
    
    # Find default index
    default_idx = None
    if default_value:
        for i, item in enumerate(items):
            if item[1] == default_value:
                default_idx = i + 1
                break
    
    # Add items to table
    for idx, item in enumerate(items, 1):
        name = item[0]
        if show_size and len(item) > 2:
            size = item[2]
            style = "bold green" if idx == default_idx else ""
            table.add_row(str(idx), f"[{style}]{name}[/{style}]" if style else name, f"{size:.2f} MB")
        else:
            style = "bold green" if idx == default_idx else ""
            table.add_row(str(idx), f"[{style}]{name}[/{style}]" if style else name)
    
    console.print(table)
    
    if default_idx:
        console.print(f"[dim]Last used: {items[default_idx-1][0]} (Option {default_idx})[/dim]")
    
    console.print()
    
    # Get selection
    try:
        prompt_msg = "[bold yellow]Select an option[/bold yellow]"
        if default_idx:
            prompt_msg += f" [dim](or press Enter for default)[/dim]"
        
        choice = IntPrompt.ask(prompt_msg, default=default_idx if default_idx else 1)
        
        if 1 <= choice <= len(items):
            return (choice - 1, items[choice - 1][1])
        else:
            console.print(f"[red]Invalid selection[/red]")
            return None
    except KeyboardInterrupt:
        return None


def get_parameter(
    name: str,
    default: Any,
    param_type: str = "int",
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    description: Optional[str] = None
) -> Any:
    """
    Get a parameter value from user with validation.
    
    Args:
        name: Parameter name
        default: Default value
        param_type: Type of parameter ("int", "float", "bool", "str")
        min_val: Minimum value (for int/float)
        max_val: Maximum value (for int/float)
        description: Optional description
    
    Returns:
        User-provided value or default
    """
    while True:
        try:
            if description:
                console.print(f"[dim]{description}[/dim]")
            
            range_info = ""
            if min_val is not None and max_val is not None:
                range_info = f" [{min_val}-{max_val}]"
            
            prompt_msg = f"[cyan]{name}[/cyan]{range_info}"
            
            if param_type == "int":
                value = IntPrompt.ask(prompt_msg, default=default)
                if min_val is not None and value < min_val:
                    console.print(f"[red]Value must be >= {min_val}[/red]")
                    continue
                if max_val is not None and value > max_val:
                    console.print(f"[red]Value must be <= {max_val}[/red]")
                    continue
                return value
            
            elif param_type == "float":
                value = FloatPrompt.ask(prompt_msg, default=default)
                if min_val is not None and value < min_val:
                    console.print(f"[red]Value must be >= {min_val}[/red]")
                    continue
                if max_val is not None and value > max_val:
                    console.print(f"[red]Value must be <= {max_val}[/red]")
                    continue
                return value
            
            elif param_type == "bool":
                return Confirm.ask(prompt_msg, default=default)
            
            else:  # str
                return Prompt.ask(prompt_msg, default=str(default))
        
        except KeyboardInterrupt:
            raise
        except Exception as e:
            console.print(f"[red]Invalid input: {e}[/red]")


def get_parameter_group(
    group_name: str,
    parameters: List[Dict[str, Any]],
    saved_values: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get a group of parameters with ability to skip all (Enter) or edit them (Tab).
    
    Args:
        group_name: Name of the parameter group
        parameters: List of parameter definitions, each with:
            - name: Parameter name
            - default: Default value
            - param_type: Type ("int", "float", "bool", "str")
            - min_val: Optional minimum value
            - max_val: Optional maximum value
            - description: Optional description
        saved_values: Dictionary of saved values
    
    Returns:
        Dictionary mapping parameter names to values
    """
    # Show current values
    console.print(f"\n[bold cyan]{group_name}[/bold cyan]")
    
    # Display current values in a table
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Parameter", style="cyan", width=30)
    table.add_column("Current Value", style="yellow")
    
    for param in parameters:
        name = param['name']
        default = saved_values.get(name, param.get('default'))
        range_info = ""
        if 'min_val' in param and 'max_val' in param:
            range_info = f" [{param['min_val']}-{param['max_val']}]"
        table.add_row(f"{name}{range_info}", str(default))
    
    console.print(table)
    console.print()
    
    # Ask if user wants to edit
    console.print("[dim]Press [bold]Enter[/bold] to use these values, [bold]Tab[/bold] to edit, or [bold]Backspace[/bold] to reset to defaults[/dim]")
    
    # Get a single keypress
    import tty
    import termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    
    try:
        tty.setraw(fd)
        k = sys.stdin.read(1)
        
        key_code = ord(k)
        
        # Check if Tab (ASCII 9), Enter (ASCII 10/13), or Backspace (ASCII 127 or 8)
        should_edit = key_code == 9  # Tab key
        should_reset = key_code in (127, 8)  # Backspace or Delete
        
        # If not tab or backspace, check for enter to accept defaults
        if not should_edit and not should_reset and key_code not in (10, 13):
            # For any other key, treat as wanting to edit
            should_edit = True
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    
    console.print()
    
    if should_reset:
        # Reset to defaults
        console.print("[yellow]↺[/yellow] Resetting to default values...")
        console.print()
        result = {}
        for param in parameters:
            name = param['name']
            result[name] = param.get('default')
        return result
    elif not should_edit:
        # Use saved values
        console.print("[green]✓[/green] Using saved values")
        result = {}
        for param in parameters:
            name = param['name']
            result[name] = saved_values.get(name, param.get('default'))
        return result
    else:
        # Edit values
        console.print("[yellow]✏[/yellow] Editing values...")
        console.print()
        result = {}
        for param in parameters:
            name = param['name']
            default = saved_values.get(name, param.get('default'))
            value = get_parameter(
                name,
                default,
                param_type=param.get('param_type', 'int'),
                min_val=param.get('min_val'),
                max_val=param.get('max_val'),
                description=param.get('description')
            )
            result[name] = value
        return result


def display_config(title: str, config: Dict[str, Any]) -> None:
    """Display configuration in a nice panel"""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="yellow")
    
    for key, value in config.items():
        # Format the key nicely
        display_key = key.replace('_', ' ').title()
        
        # Format the value
        if isinstance(value, float):
            display_value = f"{value:.2f}"
        elif isinstance(value, bool):
            display_value = "✓" if value else "✗"
        else:
            display_value = str(value)
        
        table.add_row(display_key, display_value)
    
    panel = Panel(
        table,
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED
    )
    console.print(panel)


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask for confirmation with a nice prompt"""
    return Confirm.ask(f"[bold yellow]{message}[/bold yellow]", default=default)


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a nice header"""
    console.print()
    console.rule(f"[bold cyan]{title}[/bold cyan]", style="cyan")
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]", justify="center")
    console.print()


def print_success(message: str) -> None:
    """Print a success message"""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message"""
    console.print(f"[red]✗[/red] {message}")


def print_info(message: str) -> None:
    """Print an info message"""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message: str) -> None:
    """Print a warning message"""
    console.print(f"[yellow]⚠[/yellow] {message}")
