### En lugar de tener tools definidas localmente se pueden reutilizar desde un servidor MCP
### Cualquier cliente MCP puede usar estas herramientas (sin importar Stack Tecnologico o plataforma)

from fastmcp import FastMCP
import math 
import sys

### 1.- Crear Servidor MCP
mcp = FastMCP("math")

### 2.- Tools del servidor MCP
### Requieren decorador especial de MCP 
### @mcp.tool

@mcp.tool()
def multiply(x: float, y: float) -> float:
    """Multiply x by y"""
    print(f'[Math Server] Multiply(x={x}, y={y})', file=sys.stderr)
    return x * y

@mcp.tool()
def divide(x: float, y: float) -> str:
    """Divide x by y"""
    if y == 0:
        return "Error: Division by zero"
    print(f'[Math Server] Divide(x={x}, y={y})', file=sys.stderr)
    return str(x / y)

@mcp.tool()
def add(x: float, y: float) -> float:
    """Add x and y"""
    print(f'[Math Server] Add(x={x}, y={y})', file=sys.stderr)
    return x + y

@mcp.tool()
def square_root(x: float) -> str:
    """Square root of x"""
    if x < 0:
        return 'Error: Numero negativo'
    print(f'[Math Server] Square root(x={x})', file=sys.stderr)
    return str(math.sqrt(x))

### 3.- Iniciar Servidor Local MCP
if __name__ == "__main__":
    mcp.run(transport="stdio") # transport="http" para usar en un servidor externo MCP