from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
import time
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDButton, MDButtonText
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
import os

if platform == "android":
    from android.storage import app_storage_path
    records_path = os.path.join(app_storage_path(), 'records.json')
else:
    records_dir = os.path.expanduser("~/.sudoku")
    os.makedirs(records_dir, exist_ok=True)  # 🔴 ¡Esto crea la carpeta si no existe!
    records_path = os.path.join(records_dir, 'records.json')

store = JsonStore(records_path)


from sudoku_generator import SudokuGenerator
from sudoku_puzzle import SudokuPuzzle
from sudoku_widgets import SudokuGrid, NumberPad

from kivy.uix.scatter import Scatter

class ZoomScatter(Scatter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_rotation = False  # Deshabilita la rotación (para evitar gestos innecesarios)
        self.do_translation = False  # Permitir mover con los dedos
        self.do_scale = False  # Permitir zoom con pellizco (pinch-to-zoom)
        self.auto_bring_to_front = False  # Evitar que se mueva en jerarquía de widgets
        
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.clock import Clock

class SplashScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frames = [f"data/frame_{i}.png" for i in range(1, 15)]
        self.image = Image(source=self.frames[0])
        self.add_widget(self.image)
        self.frame_index = 0
        self.max_delay = 0.12  # tiempo inicial
        self.min_delay = 0.02  # tiempo final
        self.schedule_next_frame()

    def schedule_next_frame(self):
        # Cantidad total de frames
        total_frames = len(self.frames)
        # Progreso actual como fracción (0 al 1)
        progress = self.frame_index / total_frames
        # Interpolación lineal entre max_delay y min_delay
        delay = self.max_delay - (self.max_delay - self.min_delay) * progress
        # Programar el siguiente frame con ese delay
        Clock.schedule_once(self.next_frame, delay)

    def next_frame(self, dt):
        self.frame_index += 1
        if self.frame_index >= len(self.frames):
            self.manager.current = "menu"
            return False
        self.image.source = self.frames[self.frame_index]
        self.schedule_next_frame()
        return True


class GameScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        screen_width, screen_height = Window.size
        self.font_size=min(screen_height,screen_width)*0.045
        self.sudoku_grid = None
        self.number_pad = None
        self.back_button = None
        self.timer_label = None  # Inicializar en None
        self.timer_seconds = 0  # ← Agregado para evitar el error
        self.clock_event = None  # ← Agregado para evitar el error
        self.mark_mode = False

        self.timer_label = Label(
            text="00:00",
            font_size=self.font_size,
            size_hint=(None, None)
        )
        Window.bind(size=self.update_layout)
    def start_game(self, difficulty):
        """
        Initializes a new Sudoku game based on the selected difficulty.
        """
        self.selected_difficulty = difficulty
        screen_width, screen_height = Window.size
        generator = SudokuGenerator()
        board = generator.generate_puzzle(difficulty)
        puzzle = SudokuPuzzle(board)
                # Luego de: puzzle = SudokuPuzzle(board)
        self.sudoku_puzzle = puzzle  # Guarda el puzzle en un atributo para usar en validaciones

        # Definir la cuenta inicial según la dificultad
        if difficulty == "easy":
            self.remaining_zeros_count = 40
        elif difficulty == "medium":
            self.remaining_zeros_count = 45
        elif difficulty == "hard":
            self.remaining_zeros_count = 50
        elif difficulty == "god":
            self.remaining_zeros_count = 55


        # Sudoku Grid (centrado)
        self.sudoku_grid = SudokuGrid(puzzle)

        # Panel de números (centrado abajo)
        self.number_pad = NumberPad(self.sudoku_grid)
        self.number_pad.size_hint=(None,None) 
        screen_width, screen_height = Window.size
        grid_prop = 0.75 
        pad_width = screen_width * grid_prop
        pad_height = pad_width * 0.1  # Escalar con zoom
        self.number_pad.size =(pad_width, pad_height)

        
        # Reiniciar temporizador
        self.timer_seconds = 0  
        self.timer_label.text = "00:00"

        if self.timer_label.parent:
            self.timer_label.parent.remove_widget(self.timer_label)

        # Detener temporizador anterior (si existe)
        if self.clock_event:
            Clock.unschedule(self.clock_event)
        self.clock_event = Clock.schedule_interval(self.update_timer, 1)

        # Crear botón "Main Menu"
        self.back_button = Button(
            text="Main Menu",
            font_size=self.font_size,
            size_hint=(None, None),
            background_color=(0.4, 0.4, 1, 1)
        )
        self.back_button.bind(on_release=self.go_to_menu)

        self.color_button= Button( 
            text = "Mark",
            font_size= self.font_size,
            size_hint=(None, None),
            background_color= (1,0,0,0.9 ) #red
        )
        self.color_button.bind(on_release=self.mark_cell)
        # Limpiar widgets anteriores
        self.clear_widgets()

        # Contenedor principal
        container = Widget()  # Si prefieres posicionamiento absoluto, también podrías usar FloatLayout.
        container.add_widget(self.back_button)
        container.add_widget(self.timer_label)
        container.add_widget(self.sudoku_grid)
        container.add_widget(self.number_pad)
        container.add_widget(self.color_button)
        
        
        # Envolver el contenedor en ZoomScatter para habilitar zoom y arrastre
        self.zoom_scatter = ZoomScatter(do_translation=False, do_scale=False, scale=1)
        self.zoom_scatter.scale_min = 1
        self.zoom_scatter.scale_max = 2
        self.zoom_scatter.size = (Window.width, Window.height)
        self.zoom_scatter.add_widget(container)
        
        self.zoom_scatter.bind(scale=self.on_zoom)

        self.add_widget(self.zoom_scatter)

        Clock.schedule_once(self.update_layout)
    def on_zoom(self, instance, scale):
        """🔥 Notifica a `SudokuGrid` y `NumberPad` cuando cambia el zoom"""
        # self.sudoku_grid.update_size(scale)
        # self.number_pad.update_size(scale)
    def update_layout(self, *args):
        """Actualiza la posición del menú, timer y Sudoku Grid."""
        # **Evita errores si los widgets no están creados**
        if not self.sudoku_grid or not self.back_button or not self.timer_label:
            return

        screen_width, screen_height = Window.size
        if self.zoom_scatter and len(self.zoom_scatter.children) > 0:
            container = self.zoom_scatter.children[0]  # Tomamos el primer widget
            container.size = (screen_width, screen_height)


        # Actualiza el zoom scatter para que cubra toda la pantalla
        self.zoom_scatter.pos = (0, 0)
        self.zoom_scatter.size = (screen_width, screen_height)
        
        grid_size = screen_width * 0.75

        # **Posicionar Sudoku Grid centrado**
        grid_x = (screen_width * 0.25) / 2
        grid_y = (screen_height * 0.7) / 2
        self.sudoku_grid.pos = (grid_x, grid_y)
        self.sudoku_grid.size = (grid_size, grid_size)

        # **Posicionar Panel de Números abajo centrado**
        self.number_pad.pos = (grid_x-grid_size/35,grid_y-grid_size*0.3 )
        self.number_pad.size = (grid_size, grid_size*0.3)

        
        # **Definir tamaños**
        button_width = grid_size 
        button_height = grid_size * 0.15
        timer_width = grid_size * 0.25
        timer_height = grid_size * 0.08
        spacing = grid_size * 0.05  
        
        #Boton para marcar celdas
        self.color_button.pos=  (grid_x-grid_size/35,grid_y-grid_size*0.6 )
        self.color_button.size = (button_width, button_height)
        self.color_button.font_size= grid_size*0.15

        
        # **Posicionar Botón de Menú (izquierda del Sudoku)**
        self.back_button.size = (button_width, button_height)
        self.back_button.pos = (grid_x, grid_y + grid_size + spacing+button_height)
        self.back_button.font_size= grid_size*0.15

        # **Posicionar Timer (derecha del Sudoku)**
        self.timer_label.size = (timer_width, timer_height)
        self.timer_label.pos = (grid_x + grid_size - timer_width, grid_y + grid_size + spacing)
        self.timer_label.font_size= grid_size*0.15

    def update_timer(self, dt):
        """Updates the timer every second."""
        if self.timer_label:  # ← Asegurar que el label existe antes de modificarlo
            self.timer_seconds += 1
            minutes = self.timer_seconds // 60
            seconds = self.timer_seconds % 60
            self.timer_label.text = f"{minutes:02}:{seconds:02}"

    def update_cell(self, row, col, new_value):
        """
        Actualiza la celda (row, col) con new_value y verifica si el Sudoku está completo.
        """
        # Si la celda estaba vacía (0) y ahora se asigna un número distinto de 0
        if self.sudoku_puzzle.board[row][col] == 0 and new_value != 0:
            if self.sudoku_puzzle.is_valid_move(self.sudoku_puzzle.board, row, col, new_value):
                self.remaining_zeros_count -= 1
                self.sudoku_puzzle.board[row][col] = new_value
        # Si la celda tenía un valor distinto de 0 y ahora se pasa a 0 (vacío)
        elif self.sudoku_puzzle.board[row][col] != 0 and new_value == 0:
            self.remaining_zeros_count += 1
            self.sudoku_puzzle.board[row][col] = new_value
    
        # Verificar si ya se llenaron todas las celdas
        if self.remaining_zeros_count == 0:
            # Detener el timer
            if self.clock_event:
                Clock.unschedule(self.clock_event)
    
            # Capturar el tiempo final
            timer_text = self.timer_label.text
            
            # Quitar cualquier pantalla de victoria previa, para evitar duplicados
            if self.manager.has_screen("winning"):
                old_screen = self.manager.get_screen("winning")
                self.manager.remove_widget(old_screen)
    
            # Crear la nueva pantalla de victoria, pasando timer_text y la dificultad actual
            # Asumiendo que guardaste la dificultad en self.selected_difficulty
            # (Si no lo has hecho, podrías guardarla en un atributo en start_game)
            difficulty = getattr(self, 'selected_difficulty', 'easy')
    
            winning_screen = WinningScreen(timer_text, difficulty, name="winning")
            self.manager.add_widget(winning_screen)
            self.manager.current = "winning"
            
    def go_to_menu(self, instance):
        """Returns to the main menu and clears the game screen."""
        if self.clock_event:
            Clock.unschedule(self.clock_event)  # Detener temporizador si existe
        self.clear_widgets()
        self.manager.current = "menu"

    def mark_cell(self, instance):
        if self.mark_mode:
            self.color_button.background_color = (1, 0, 0, 1)  # Rojo encendido
        else:
            self.color_button.background_color = (1, 0, 0, 0.4)  # Rojo apagado
        self.mark_mode = not self.mark_mode



############-----------#############
            #MENU SCREEN
############-----------#############


class MenuScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        Window.bind(on_resize=self.update_positions)
        self.create_buttons()

    def create_buttons(self):
        self.layout.clear_widgets()

        screen_width, screen_height = Window.size
        button_width = screen_width * (2 / 5)
        button_height = button_width / 1.8
        spacing = screen_height * 0.02

        difficulty_colors = {
            "Easy": (0.1, 0.7, 0.2, 1),              # Verde más suave
            "Medium": (0.2, 0.4, 1.0, 1),             # Azul brillante
            "Hard": (230 / 255, 218 / 255, 0, 0.8),   # Amarillo fuerte
            "God": (0.8, 0.1, 0.1, 1)                 # Rojo intenso
        }

        for i, difficulty in enumerate(["Easy", "Medium", "Hard", "God"]):
            y_offset = screen_height * 0.6 - (i * (button_height + spacing))

            btn = MDButton(
                style="outlined",
                size_hint=(None, None),
                size=(button_width, button_height),
                pos=((screen_width - button_width) / 2, y_offset),
                radius=[20, 20, 0, 20],
                theme_bg_color="Custom",
                md_bg_color=difficulty_colors[difficulty],
            )

            # Contenedor para el texto con borde
            text_container = FloatLayout(size_hint=(1, 1))

            # Texto de borde (negro)
            btn_text_border = Label(
                text=difficulty,
                font_size=button_width * 0.215,
                color=(0, 0, 0, 1),
                halign="center",
                valign="middle",
                size_hint=(1, 1),
                pos_hint={"center_x": 0.5, "center_y": 0.5}
            )
            btn_text_border.bind(
                size=lambda instance, value: setattr(instance, 'text_size', value)
            )

            # Texto principal (blanco)
            btn_text = Label(
                text=difficulty,
                font_size=button_width * 0.21,
                color=(1, 1, 1, 1),
                halign="center",
                valign="middle",
                size_hint=(1, 1),
                pos_hint={"center_x": 0.5, "center_y": 0.5}
            )
            btn_text.bind(
                size=lambda instance, value: setattr(instance, 'text_size', value)
            )

            text_container.add_widget(btn_text_border)
            text_container.add_widget(btn_text)
            btn.add_widget(text_container)

            btn.difficulty = difficulty
            btn.bind(on_release=self.on_difficulty_selected)
            self.layout.add_widget(btn)

        # Botón de opciones avanzadas
        adv_btn_width = button_width * 0.8
        adv_btn_height = button_height * 0.5

        adv_btn = MDButton(
            style="elevated",
            size_hint=(None, None),
            size=(adv_btn_width, adv_btn_height),
            pos=((screen_width - adv_btn_width) / 2, screen_height * 0.04),
            radius=[20, 20, 20, 20],
            theme_bg_color="Custom",
            md_bg_color=(0.3, 0.3, 0.3, 1),
        )

        adv_btn_text = MDButtonText(
            text="Advanced Options",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )
        adv_btn.add_widget(adv_btn_text)
        adv_btn.bind(on_release=self.go_to_options)
        self.layout.add_widget(adv_btn)

    def update_positions(self, *args):
        self.create_buttons()

    def on_difficulty_selected(self, button):
        selected_difficulty = button.difficulty.lower()
        self.manager.get_screen("game").start_game(selected_difficulty)
        self.manager.current = "game"

    def go_to_options(self, instance):
        self.manager.current = "options"

    def on_pre_enter(self):
        self.create_buttons()


############-----------#############
            #OPTIONS SCREEN
############-----------#############

class AppOptions(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        self.add_widget(layout)

        screen_width, screen_height = Window.size
        button_width = screen_width * 0.3
        button_height = button_width*0.4

        # 🔴 Botón para resetear récords
        reset_btn = Button(
            text="Reset Records",
            size_hint=(None, None),
            size=(button_width, button_height),
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            background_color=(0.7, 0, 0, 1),
            font_size=button_width * 0.15
        )
        reset_btn.bind(on_release=self.reset_records)

        # 🔙 Botón para volver al menú
        back_btn = Button(
            text="Back to Menu",
            size_hint=(None, None),
            size=(button_width, button_height),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            background_color=(0.2, 0.2, 0.8, 1),
            font_size=button_width * 0.15
        )
        back_btn.bind(on_release=self.go_back_to_menu)

        layout.add_widget(reset_btn)
        layout.add_widget(back_btn)

    def reset_records(self, instance):
        store.clear()
        store.store_sync()


    def go_back_to_menu(self, instance):
        self.manager.current = "menu"



from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window

############-----------#############
            #WINNING SCREEN
############-----------#############

class WinningScreen(MDScreen):
    """
    Pantalla de victoria que recibe el tiempo final y la dificultad,
    y se encarga de actualizar el récord en records.json.
    """
    def __init__(self, timer_text, difficulty, **kwargs):
        super().__init__(**kwargs)
        self.timer_text = timer_text
        self.difficulty = difficulty

        # Guardar/actualizar récord
        self.save_record()

        # Contenedor raíz
        self.root_layout = FloatLayout(size_hint=(1, 1))

        # BoxLayout centrado, más arriba
        self.box = BoxLayout(
            orientation='vertical',
            spacing=2,
            padding=2,
            size_hint=(0.8, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )

        # Etiquetas y botón
        self.title_label = Label(text="Completed!", halign="center")
        self.timer_label = Label(text='time: ' + timer_text, halign="center")
        self.menu_button = Button(
            text="Main Menu",
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 1}
        )
        self.menu_button.bind(on_release=self.go_to_menu)

        # Agregamos widgets
        self.box.add_widget(self.title_label)
        self.box.add_widget(self.timer_label)
        self.box.add_widget(self.menu_button)

        # Añadir al FloatLayout y luego a la Screen
        self.root_layout.add_widget(self.box)
        self.add_widget(self.root_layout)

        # Redimensión dinámica
        Window.bind(size=self._update_layout)
        self._update_layout(None, None)

    def save_record(self):
        """
        Guarda o actualiza el récord en records.json para la dificultad dada.
        """
        record_key = f"record_{self.difficulty.lower()}"
        try:
            new_minutes, new_seconds = map(int, self.timer_text.split(':'))
        except ValueError:
            # Si el formato del tiempo no es mm:ss, abortar
            return

        # Si había un tiempo anterior, solo lo reemplazamos si el nuevo es menor
        if store.exists(record_key):
            old_time = store.get(record_key)['time']  # Ejemplo: "04:12"
            old_minutes, old_seconds = map(int, old_time.split(':'))
            if (new_minutes, new_seconds) < (old_minutes, old_seconds):
                store.put(record_key, time=self.timer_text)
        else:
            # Si no existía, lo creamos
            store.put(record_key, time=self.timer_text)

    def _update_layout(self, instance, size):
        # Ajusta el tamaño de fuentes y del botón al cambiar la ventana
        base = min(Window.width, Window.height)
        self.title_label.font_size = base * 0.1
        self.timer_label.font_size = base * 0.08
        self.menu_button.size = (base * 0.5, base * 0.2)
        self.menu_button.font_size = base * 0.08

    def go_to_menu(self, instance):
        self.manager.current = "menu"



from kivymd.app import MDApp
class SudokuApp(MDApp):
    def build(self):
        screen_width, screen_height = Window.system_size  # Obtiene la resolución del monitor
        aspect_ratio = 9/19.5  # Relación de aspecto típica de un celular

        # Ajustar el tamaño de la ventana manteniendo la proporción
        if screen_width / screen_height > aspect_ratio:
            Window.size = (screen_height * aspect_ratio, screen_height * 0.9)  # Basado en altura
        else:
            Window.size = (screen_width * 0.9, screen_width / aspect_ratio)  # Basado en ancho


        sm = ScreenManager()
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(AppOptions(name="options"))
        sm.current = "splash"

        return sm


if __name__ == '__main__':
    SudokuApp().run()

