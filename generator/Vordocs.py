import os
import pathlib
import pygame

TITLE: str = "Vordocs"
VERSION: str = "0.0.1"

UISCALE: float = 1
FONT: str = "consolas"

class Colors:
    black = (0, 0, 0)
    background1 = (37, 37, 37, 255)
    text1 = (190, 190, 190, 255)


class FileManager:
    """
    The FileManager will automatically handle finding, parsing, and exporting markdown files.
    """

    possiblePaths: list[tuple[str, str]] = [
        (".", "../content"),   # "if Vordocs.py found in [0], then content is under [1]"
        ("generator", "content")
    ]

    def __init__(self):
        self.contentRoot: pathlib.Path = pathlib.Path()
        self.vorRoot: pathlib.Path = pathlib.Path()

        print("[FileManager] Searching for content root...")
        for possible in self.possiblePaths:
            if (pathlib.Path(possible[0]) / "Vordocs.py").is_file():
                self.vorRoot = pathlib.Path(possible[0])
                self.contentRoot = pathlib.Path(possible[1])
                break
        else:
            raise FileNotFoundError("[FileManager] Unable to find root!")

        print(f"[FileManager] Vordocs found at '{str(self.vorRoot)}'")
        print(f"[FileManager] Content found at '{str(self.contentRoot)}'")

    def getSymbol(self, name: str) -> pygame.Surface:
        return pygame.image.load(self.vorRoot / "symbols" / name).convert_alpha()
        


class Documentation:
    MODE_READONLY = 0
    MODE_EDIT = 1

    class Item:
        FOLDER = 0
        CLASS = 1
        DATATYPE = 2
        GLOBAL = 3

        def __init__(self, itemType: int, name: str, filePath: str) -> None:
            self.itemType: int = itemType
            self.Name: str = name

            self.indent: int = 0
            self.index: int = 0

            if itemType > 0:
                f = open(filePath, "r")
                self.text: str = f.read()
                f.close()

            self.children: list[Documentation.Item] = []
            self.Open: bool = False


    def __init__(self, fM: FileManager, mode: int):
        if (mode == self.MODE_EDIT):
            raise NotImplementedError("File Editting has not been implemented")

        self.File: FileManager = fM

        self.x = 0
        self.y = 0
        self.scroll = 0

        self.idxSpacing = 20 * UISCALE
        self.indSpacing = 30 * UISCALE
        self.arrowSize = 20 * UISCALE
        self.iconSize = self.arrowSize

        self.font = pygame.font.SysFont(FONT, int(20 * UISCALE))

        # Build File Tree
        print("[Documentation] Building FileTree")
        self.Explorer: list[Documentation.Item] = []
        self.drawList: list[Documentation.Item] = []
        self.totalItems: int = 0

        tree: list[str] = ["reference"]
        self.parseFolder(tree, self.Explorer)
        print(f"[Documentation] Scanned {self.totalItems} items")

        # Icons
        self.Icons: list[pygame.Surface] = [
            pygame.transform.scale(self.File.getSymbol("folder.png"), (self.iconSize, self.iconSize)),
            pygame.transform.scale(self.File.getSymbol("class.png"), (self.iconSize, self.iconSize)),
            pygame.transform.scale(self.File.getSymbol("datatype.png"), (self.iconSize, self.iconSize)),
            pygame.transform.scale(self.File.getSymbol("global.png"), (self.iconSize, self.iconSize)),
            pygame.transform.scale(self.File.getSymbol("generic.png"), (self.iconSize, self.iconSize)),
        ]
        self.arrowClosed = pygame.transform.scale(self.File.getSymbol("arrowClosed.png"), (self.arrowSize, self.arrowSize))
        self.arrowOpen = pygame.transform.scale(self.File.getSymbol("arrowOpen.png"), (self.arrowSize, self.arrowSize))

        self.update()

    def parseFolder(self, tree: list[str], parent: list[Item]):
        folder: str = str(self.File.contentRoot) + "/" + "/".join(tree)

        docFolder: Documentation.Item = self.Item(self.Item.FOLDER, tree[-1], folder)
        parent.append(docFolder)

        for item in os.listdir(folder):
            path = pathlib.Path(folder + "/" + item)

            if path.is_dir():
                tree.append(item)
                self.parseFolder(tree, docFolder.children)
                tree.pop(-1)
            else:
                self.parseItem(item, str(path), docFolder)

    def parseItem(self, name: str, path: str, parent: Item):
        itemType = -1

        if parent.Name == "classes":
            itemType = self.Item.CLASS
        elif parent.Name == "datatypes":
            itemType = self.Item.DATATYPE
        elif parent.Name == "globals":
            itemType = self.Item.GLOBAL

        newItem: Documentation.Item = self.Item(itemType, name, path)
        parent.children.append(newItem)

        self.totalItems += 1

    def _update(self, idx: int, idn: int, item: Item) -> int:
        item.index = idx
        item.indent = idn
        self.drawList.append(item)

        print(item.Name, item.index, item.indent)

        idx += 1

        if item.Open or True:
            idn += 1

            for child in item.children:
                idx = self._update(idx, idn, child)

            idn -= 1

        return idx

    def update(self):
        self.drawList.clear()
        self._update(0, 0, self.Explorer[0])

    def draw(self, surface: pygame.Surface):
        for item in self.drawList:
            x = self.x + item.indent * self.indSpacing
            y = self.y + item.index * self.idxSpacing - self.scroll

            if (len(item.children) > 0):
                img = self.arrowOpen if item.Open else self.arrowClosed
                surface.blit(img, (x, y))

            x += self.arrowSize
            surface.blit(self.Icons[item.itemType], (x, y))

            x += self.iconSize
            surface.blit(self.font.render(item.Name, True, Colors.text1), (x, y))



class Window:
    def __init__(self, width: int, height: int):
        self.File: FileManager = FileManager()

        self.width: int = width
        self.height: int = height

        self.window: pygame.Surface = pygame.display.set_mode((width, height))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        pygame.display.set_caption(f"{TITLE} - v{VERSION}")
        pygame.display.set_icon(self.File.getSymbol("logo.png"))

        self.ExplorerSurface: pygame.Surface = pygame.Surface((width, height), pygame.SRCALPHA)

        self.running = True
        self.mx, self.my = -100, -100
        
        self.Docs: Documentation = Documentation(self.File, Documentation.MODE_READONLY)

    def handleEvents(self):
        # self.mx, self.my = pygame.mouse.get_pos()
        # keys = pygame.key.get_pressed()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False

    def step(self):
        self.ExplorerSurface.fill(Colors.background1)
        self.handleEvents()

        self.Docs.draw(self.ExplorerSurface)

        self.window.fill(Colors.black) # <--
        self.window.blit(self.ExplorerSurface, (0, 0))

        pygame.display.flip()
        self.clock.tick(60)


def main():
    pygame.display.init()
    pygame.font.init()

    w, h = pygame.display.get_desktop_sizes()[0]

    win = Window(int(w / 1.5), int(h / 1.5))

    while (win.running):
        win.step()

    pygame.quit()


if __name__ == "__main__":
    main()