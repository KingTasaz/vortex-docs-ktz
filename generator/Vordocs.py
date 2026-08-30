import os
import pathlib
import pygame
from typing import Any

TITLE: str = "Vordocs"
VERSION: str = "0.0.2"

UISCALE: float = 1
FONT: str = "consolas"

class Colors:
    black = (0, 0, 0)
    background1 = (37, 37, 37, 255)
    background2 = (57, 57, 57, 255)
    text1 = (190, 190, 190, 255)
    hover1 = (255, 255, 255, 100)


# MARK: File Manager
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
        


# MARK: Documentation
class Documentation:
    MODE_READONLY = 0
    MODE_EDIT = 1

    class DocData:
        def __init__(self) -> None:
            pass    # title, description, revision, summary, sections, etc...

    class Item:
        FOLDER = 0
        CLASS = 1
        DATATYPE = 2
        GLOBAL = 3

        def __init__(self, itemType: int, name: str, filePath: str, data: Any | None = None) -> None:
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

            self.Rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

            if data is not None:
                self.Data: Documentation.DocData = data

        def draw(self, surface: pygame.Surface):
            ...


    def __init__(self, fM: FileManager, mode: int, windowWidth: int, windowHeight: int):
        if (mode == self.MODE_EDIT):
            raise NotImplementedError("File Editting has not been implemented")

        self.File: FileManager = fM

        self.x = 0
        self.y = 0
        self._scroll = 0

        self.idxSpacing = 20 * UISCALE
        self.indSpacing = 30 * UISCALE
        self.arrowSize = 20 * UISCALE
        self.iconSize = self.arrowSize

        self.ww = windowWidth
        self.wh = windowHeight

        self.explorerWidth = 400 * UISCALE

        self.font = pygame.font.SysFont(FONT, int(20 * UISCALE))

        self.mx, self.my = -100, -100

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

        # Menus
        self.selectedItem: Documentation.Item | None = None

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

        idx += 1

        if item.Open:
            idn += 1

            for child in item.children:
                idx = self._update(idx, idn, child)

            idn -= 1

        return idx

    def update(self):
        self.drawList.clear()
        self._update(0, 0, self.Explorer[0])

    def draw(self, surface: pygame.Surface):
        self._scroll = max(self._scroll, self.getScrollMax())
        self._scroll = min(self._scroll, 0)

        pygame.draw.rect(
            surface,
            Colors.background2,
            (self.x, self.y, self.explorerWidth, self.wh)
        )

        for item in self.drawList:
            x = self.x + item.indent * self.indSpacing
            y = self.y + item.index * self.idxSpacing + self._scroll

            x0 = x

            if (len(item.children) > 0):
                img = self.arrowOpen if item.Open else self.arrowClosed
                surface.blit(img, (x, y))

            x += self.arrowSize
            surface.blit(self.Icons[item.itemType], (x, y))

            x += self.iconSize
            text: pygame.Surface = self.font.render(item.Name, True, Colors.text1)
            surface.blit(text, (x, y))

            item.Rect.x = x0
            item.Rect.y = y
            item.Rect.w = self.explorerWidth - x0
            item.Rect.h = self.iconSize

            if item.Rect.collidepoint(self.mx, self.my):
                temp = pygame.Surface((item.Rect.w, item.Rect.h), pygame.SRCALPHA)
                pygame.draw.rect(temp, Colors.hover1, temp.get_rect(), border_radius=10)
                surface.blit(temp, (item.Rect.x, item.Rect.y))
                # temp is required for transparency

        if self.selectedItem is not None:
            self.selectedItem.draw(surface)

    def mouse(self, x: int, y: int, click: bool, isRight: bool = False):
        self.mx = x
        self.my = y

        if x > self.explorerWidth:
            return

        if not click:
            return

        for item in self.drawList:
            if not item.Rect.collidepoint(self.mx, self.my):
                continue

            if item.itemType == self.Item.FOLDER:
                item.Open = not item.Open
            else:
                self.selectedItem = item

            break
        else:
            self.selectedItem = None

        self.update()

    def scroll(self, scrollAmount: int):
        self._scroll += scrollAmount

    def getScrollMax(self) -> int:
        return -int(max(self.idxSpacing * len(self.drawList) - self.wh, 0))



# MARK: Window
class Window:
    def __init__(self, width: int, height: int):
        self.File: FileManager = FileManager()

        # Variables
        self.width: int = width
        self.height: int = height

        self.running = True
        self.mx, self.my = -100, -100

        # Pygame
        self.window: pygame.Surface = pygame.display.set_mode((width, height))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        pygame.display.set_caption(f"{TITLE} - v{VERSION}")
        pygame.display.set_icon(self.File.getSymbol("logo.png"))

        # Pygame Variables
        self.ExplorerSurface: pygame.Surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.labelFont = pygame.font.SysFont(FONT, int(32 * UISCALE))

        # Objects
        self.setLabel("Loading Documentation...")
        self.Docs: Documentation = Documentation(self.File, Documentation.MODE_READONLY, self.width, self.height)

    def handleEvents(self):
        self.mx, self.my = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        self.Docs.mouse(self.mx, self.my, False)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == pygame.BUTTON_LEFT:
                    self.Docs.mouse(self.mx, self.my, True)
                elif e.button == pygame.BUTTON_RIGHT:
                    self.Docs.mouse(self.mx, self.my, True, isRight=True)
            elif e.type == pygame.MOUSEWHEEL:
                self.Docs.scroll(e.y * 30)

    def step(self):
        self.ExplorerSurface.fill(Colors.background1)
        self.handleEvents()

        self.Docs.draw(self.ExplorerSurface)

        self.window.fill(Colors.black) # <--
        self.window.blit(self.ExplorerSurface, (0, 0))

        pygame.display.flip()
        self.clock.tick(60)

    def setLabel(self, labelText: str):
        text: pygame.Surface = self.labelFont.render(labelText, True, Colors.text1)
        x = self.width / 2 - text.get_width() / 2
        y = self.height / 2 - text.get_height() / 2

        self.window.fill(Colors.background1)
        self.window.blit(text, (x, y))
        pygame.display.flip()


def main():
    pygame.display.init()
    pygame.font.init()

    w, h = pygame.display.get_desktop_sizes()[0]

    win = Window(int(w / 1.2), int(h / 1.2))

    while (win.running):
        win.step()

    pygame.quit()


if __name__ == "__main__":
    main()