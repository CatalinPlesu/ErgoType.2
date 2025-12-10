"""
Rich-based interactive menu system for ErgoType.2
Provides a nicer user interface with colors, tables, and panels.
"""

import sys
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


console = Console()


class RichMenu:
    """Interactive menu using Rich library for better UI"""
    
    def __init__(self, title: str = "Menu"):
        self.title = title
        self.items: List[Tuple[str, Callable]] = []
    
    def add_item(self, title: str, func: Callable) -> None:
        """Add a menu item with title and callback function"""
        self.items.append((title, func))
    
    def display(self) -> None:
        """Display the menu and get user selection"""
        while True:
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
            
            # Add menu items
            for idx, (item_title, _) in enumerate(self.items, 1):
                table.add_row(str(idx), item_title)
            table.add_row("0", "[red]Exit[/red]")
            
            console.print(table)
            console.print()
            
            # Get user choice
            try:
                choice = IntPrompt.ask(
                    "[bold yellow]Select an option[/bold yellow]",
                    default=0
                )
                
                if choice == 0:
                    console.print("[yellow]Exiting...[/yellow]")
                    break
                elif 1 <= choice <= len(self.items):
                    console.clear()
                    _, func = self.items[choice - 1]
                    try:
                        func()
                    except KeyboardInterrupt:
                        console.print("\n[yellow]Operation cancelled[/yellow]")
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")
                        import traceback
                        traceback.print_exc()
                    
                    console.print()
                    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                else:
                    console.print(f"[red]Invalid choice. Please select 0-{len(self.items)}[/red]")
                    console.input("[dim]Press Enter to continue...[/dim]")
            except KeyboardInterrupt:
                console.print("\n[yellow]Exiting...[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                console.input("[dim]Press Enter to continue...[/dim]")


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
