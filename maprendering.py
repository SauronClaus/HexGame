from Constants import HEX_SIZE
from Constants import ROOT_3
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line, Rectangle
from kivy.core.text import Label as CoreLabel
import Globals
import ini
from FogControl import Fog_Controller

SHOW_COORDINATES = False


# widget that draws hex maps
class HexMapWidget(FloatLayout):
    def __init__(self, in_hex_map, in_gamescreen, **kwargs):
        super(HexMapWidget, self).__init__(**kwargs)
        self.hex_map = in_hex_map
        self.gamescreen = in_gamescreen
        self.size = self.minimum_size()
        self.hex_outline_segments = []
        self.editor = None
        print("width " + str(self.size[0]) + " height " + str(self.size[1]))
        self.canvas.after.clear()
        self.visible_y_bottom = 0
        self.visible_y_top = 0
        self.visible_x_left = 0
        self.visible_x_right = 0
        self.visible_area_bottom_left = None
        self.visible_area = []
        self.terrain_layout = None
        self.structure_layout = None
        self.container_structure_layout = None
        self.unit_layout = None
        self.fog_controller = Fog_Controller(self.hex_map)
        self.do_scroll_x = True
        self.do_scroll_y = True

    def update_canvas(self, *args):
        print("Updating canvas with widgets")
        for widget in self.children:
            # Print basic details about each widget
            print(f"Widget: {widget.__class__.__name__}, Size: {widget.size}, Position: {widget.pos}")
        self.canvas.clear()
        self.canvas.after.clear()
        self.canvas.before.clear()
        if self.terrain_layout is not None:
            self.terrain_layout.clear_widgets()
            self.terrain_layout = None
        if self.structure_layout is not None:
            self.structure_layout.clear_widgets()
            self.structure_layout = None
        if self.unit_layout is not None:
            self.unit_layout.clear_widgets()
            self.unit_layout = None
        if self.container_structure_layout is not None:
            self.container_structure_layout.clear_widgets()
            self.container_structure_layout = None
        self.fog_controller.reset_layout()

        self.clear_widgets()
        self.size = (0.75 * HEX_SIZE * self.hex_map.grid_width, 0.5 * ROOT_3 * HEX_SIZE * self.hex_map.grid_height)
        hint = (1.33/self.hex_map.grid_width, 1.33/self.hex_map.grid_height)
        print(f"hint {1.33/self.hex_map.grid_width}")
        layout_pos = (0.0, 0.0)
        self.terrain_layout = FloatLayout(size_hint=hint, pos=layout_pos)
        self.add_widget(self.terrain_layout)

        # add hex backgrounds
        self.place_terrain_images()

        # draw  grid
        self.draw_hex_grid()

        # add rivers
        self.place_rivers()

        # add roads
        self.place_roads()

        # add structures
        self.place_structure_images()

        self.structure_layout = FloatLayout(size_hint=hint, size=self.size, pos=layout_pos)
        self.add_widget(self.structure_layout)
        self.unit_layout = FloatLayout(size_hint=hint, size=self.size, pos=layout_pos)
        self.add_widget(self.unit_layout)
        self.container_structure_layout = FloatLayout(size_hint=hint, size=self.size, pos=layout_pos)
        self.add_widget(self.container_structure_layout)
        self.add_widget(self.fog_controller.layout)

        self.fog_controller.place_fog_war()
        self.fog_controller.render_fog_war()

        # add outline
        self.place_outline()

        print("add visible widgets")
        self.visible_area.clear()
        for column in self.hex_map.hex_grid:
            for hexagon in column:
                hexagon.mark_visible = False
        self.add_visible_widgets()
        for widget in self.children:
            # Print basic details about each widget
            print(f"Widget: {widget.__class__.__name__}, Size: {widget.size}, Position: {widget.pos}")

    def add_visible_widgets(self):
        if SHOW_COORDINATES:
            return 0
        num_widgets = 0
        # add widgets in viewable area
        self.update_visibility_position()

        for column in self.hex_map.hex_grid:
            for hexagon in column:
                if self.hex_is_in_visible_area(hexagon) and not hexagon.mark_visible:
                    self.visible_area.append(hexagon)
                    hexagon.mark_visible = True
                    if hexagon.terrain_image.parent is None:
                        if hexagon.terrain_image is not None:
                            self.add_terrain_widget(hexagon.terrain_image)
                        if hexagon.structure_image is not None:
                            self.add_structure_widget(hexagon.structure_image, hexagon.structure)
                            num_widgets += 1
                        for unit in hexagon.game_units:
                            if (unit.sprite is not None) and ((hexagon.fog_level[Globals.LOCAL_PLAYER] == 0) or ini.NO_FOG):
                                self.add_unit_widget(unit.sprite)
                                num_widgets += 1
                        if hexagon.fog_image is not None:
                            self.fog_controller.add_fog_widget(hexagon.fog_image)
                            num_widgets += 1
        # print(f"TOTAL WIDGETS {num_widgets}")
        return num_widgets

    def add_terrain_widget(self, new_widget):
        self.terrain_layout.add_widget(new_widget)

    def add_structure_widget(self, new_widget, structure):
        if (structure is None) or not structure.container_structure:
            self.structure_layout.add_widget(new_widget)
        else:
            self.container_structure_layout.add_widget(new_widget)

    def add_unit_widget(self, new_widget):
        self.unit_layout.add_widget(new_widget)

    def hex_is_in_visible_area(self, hexagon):
        hex_offset_x, hex_offset_y = hexagon.get_hex_center()
        return (hex_offset_x + HEX_SIZE > self.visible_x_left) and (hex_offset_x - HEX_SIZE < self.visible_x_right) and (hex_offset_y + HEX_SIZE > self.visible_y_bottom) and (hex_offset_y - HEX_SIZE < self.visible_y_top)

    def update_visibility_position(self):
        scrollview = self.gamescreen.scroll_view
        self.visible_y_bottom = max(0.0, scrollview.scroll_y * (scrollview.viewport_size[1] - scrollview.height))
        # print(f"visible_y_bottom {self.visible_y_bottom} scroll_y {scrollview.scroll_y} viewport size {scrollview.viewport_size[1]} height {scrollview.height}")
        self.visible_y_top = self.visible_y_bottom + scrollview.height
        self.visible_x_left = max(0.0, scrollview.scroll_x * (scrollview.viewport_size[0] - scrollview.width))
        self.visible_x_right = self.visible_x_left + scrollview.width
        self.visible_area_bottom_left = self.hex_map.find_hex_at_position(self.visible_x_left, self.visible_y_bottom)
        # if self.visible_area_bottom_left is not None:
        #    print(f"find hex at {self.visible_x_left}, {self.visible_y_bottom} found {self.visible_area_bottom_left.index_x} {self.visible_area_bottom_left.index_y}")
        # else:
        #    print(f"find hex at {self.visible_x_left}, {self.visible_y_bottom} found None")

    # PRIVATE helper for remove_hex_widgets()
    def remove_hex_widget(self, widget):
        if (widget is not None) and (widget.parent is not None):
            widget.parent.remove_widget(widget)

    def remove_hex_widgets(self, hexagon):
        hexagon.mark_visible = False
        self.remove_hex_widget(hexagon.terrain_image)
        self.remove_hex_widget(hexagon.structure_image)
        self.remove_hex_widget(hexagon.terrain_image)
        self.remove_hex_widget(hexagon.terrain_image)
        for unit in hexagon.game_units:
            self.remove_hex_widget(unit.sprite)
        self.remove_hex_widget(hexagon.fog_image)

    def update_visible_widgets(self):
        old_visible_area = self.visible_area_bottom_left
        self.update_visibility_position()
        # print(f"update_visible_widgets {self.gamescreen.scroll_view.scroll_x} {self.gamescreen.scroll_view.scroll_y}")
        if old_visible_area != self.visible_area_bottom_left:
            # remove widgets associated with hexes that just became not visible
            for hexagon in self.visible_area:
                if not self.hex_is_in_visible_area(hexagon):
                    self.visible_area.remove(hexagon)
                    self.remove_hex_widgets(hexagon)
            # add widgets associated with hexes that just became visible
            self.add_visible_widgets()

    def minimum_size(self):
        width = self.hex_map.grid_width * HEX_SIZE * 1.5
        height = self.hex_map.grid_height * HEX_SIZE * ROOT_3 * 0.5
        return width, height

    def draw_hex_grid(self):
        with self.canvas:
            Color(10, 10, 10)
            print(f"draw hex grid width {len(self.hex_map.hex_grid)}")
            for y, column in enumerate(self.hex_map.hex_grid):
                for x, hexagon in enumerate(column):
                    # vs {hexagon.index_x} {hexagon.index_y}
                    self.draw_hexagon(hexagon)

    def draw_hexagon(self, hexagon):
        # print("draw at " + str(x) + " " + str(y))
        # calculate height of triangle with side from left or right of hexagon
        x, y = hexagon.get_hex_position()
        triangle_height = 0.25 * ROOT_3 * HEX_SIZE
        points = [x, y - triangle_height, x + 0.25 * HEX_SIZE, y, x + 0.75 * HEX_SIZE, y, x + HEX_SIZE, y - triangle_height]
        Line(points=points, width=1, close=False)

        if SHOW_COORDINATES:
            # Draw the position text inside the hexagon
            pos_text = f"{hexagon.index_x}, {hexagon.index_y}"  # Position text in the format "x, y"
            label = CoreLabel(text=pos_text, font_size=12, color=(0, 0, 0, 1))
            label.refresh()
            text_texture = label.texture
            text_pos = (x + 0.5 * HEX_SIZE - text_texture.size[0] / 2, y - triangle_height - text_texture.size[1] / 2)
            Rectangle(texture=text_texture, pos=text_pos, size=text_texture.size)

    def place_terrain_images(self):
        print("place terrain images")
        num = 0
        for column in self.hex_map.hex_grid:
            for hexagon in column:
                hexagon.update_terrain_image()
        return num

    def place_structure_images(self):
        print("place structure images")
        num = 0
        for column in self.hex_map.hex_grid:
            for hexagon in column:
                hexagon.update_structure_image()
        return num

    def place_rivers(self):
        for column in self.hex_map.hex_grid:
            for hexagon in column:
                self.draw_rivers(hexagon)

    def place_outline(self):
        for line_segment in self.hex_outline_segments:
            line_segment.group = "Outlines"
        self.hex_outline_segments.clear()

        with self.canvas.after:
            self.canvas.after.remove_group("Outlines")
            for y, column in enumerate(self.hex_map.hex_grid):
                for x, hexagon in enumerate(column):
                    if hexagon.should_outline:
                        Color(1.0, 1.0, 0.0)
                        # print(f"{hexagon.index_x}, {hexagon.index_y} outline drawn.")
                        self.draw_outline(hexagon, 2)
                    elif hexagon.path_outline:
                        Color(0.6, 0.6, 0.6)
                        self.draw_outline(hexagon, 2)
                    elif hexagon.search_outline:
                        Color(0.6, 0.1, 0.1)
                        self.draw_outline(hexagon, 2)

    def place_roads(self):
        print("place roads")
        if SHOW_COORDINATES:
            return
        for y, column in enumerate(self.hex_map.hex_grid):
            for x, hexagon in enumerate(column):
                for other_hexagon in hexagon.road_connections:
                    self.draw_road(hexagon, other_hexagon)

    def draw_road(self, hexagon, other_hex):
        pos_x, pos_y = hexagon.get_hex_center()
        other_x, other_y = other_hex.get_hex_center()
        points = [pos_x, pos_y, other_x, other_y]
        with self.terrain_layout.canvas.after:
            Color(0.5, 0.5, 0.0)
            Line(points=points, width=3, close=False)

    def draw_rivers(self, hexagon):
        if hexagon.river_edges[0] or hexagon.river_edges[1] or hexagon.river_edges[2] or hexagon.river_edges[3] or hexagon.river_edges[4] or hexagon.river_edges[5]:
            hex_vertex_x, hex_vertex_y = hexagon.get_hex_vertices()
            for index in range(len(hexagon.river_edges)):
                self.draw_river_edge(index, hex_vertex_x, hex_vertex_y)

    def draw_river_edge(self, hexagon, index, hex_vertex_x, hex_vertex_y):
        if hexagon.river_edges[index]:
            points = [hex_vertex_x[index], hex_vertex_y[index], hex_vertex_x[(index + 1) % 6],
                      hex_vertex_y[(index + 1) % 6]]
            with self.canvas.after:
                Color(0.0, 0.0, 1.0)
                Line(points=points, width=7, close=False)

    def draw_outline(self, hexagon, width):
        hex_vertex_x, hex_vertex_y = hexagon.get_hex_vertices()
        for index in range(6):
            points = [hex_vertex_x[index], hex_vertex_y[index], hex_vertex_x[(index + 1) % 6], hex_vertex_y[(index + 1) % 6]]
            with self.canvas.after:
                new_line = Line(points=points, width=width, close=False)
                self.hex_outline_segments.append(new_line)
