from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mini-example")


@mcp.tool()
def saludar(nombre: str) -> str:
    """Devuelve un saludo simple."""
    return f"Hola, {nombre}"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
