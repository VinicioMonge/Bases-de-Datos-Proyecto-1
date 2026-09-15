import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

import customtkinter as ctk
import psycopg2

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppAgenda(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Agenda 3 Patitos")
        self.geometry("1216x684")
        self.minsize(1024, 576)

        self.conn_params = {
            "dbname": "agenda",
            "user": "postgres",
            "password": "postgres",
            "host": "localhost",
            "port": "5432",
        }

        self.usuarios_combo = {}
        self.categorias_combo = {}
        self.ubicaciones_combo = {}
        self.categorias_padre_combo = {}
        self.eventos_combo = {}
        self.estados_combo = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.crear_sidebar()
        self.crear_area_principal()
        self.configurar_estilos()

        self.actualizar_todas_las_tablas()

        if DateEntry is None:
            self.after(500, lambda: messagebox.showwarning(
                "Calendario no instalado",
                "Para usar los selectores de fecha instala:\n\npip install tkcalendar"
            ))

    # -------------------- INFRAESTRUCTURA --------------------

    def obtener_conexion(self):
        conn = psycopg2.connect(**self.conn_params)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO prototipo, public;")
        return conn

    def ejecutar_consulta(self, sql, params=None, fetch=False):
        conn = None
        try:
            conn = self.obtener_conexion()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall() if fetch else None
            conn.commit()
            return rows
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def configurar_estilos(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def crear_treeview(self, parent, columnas, widths):
        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        tree = ttk.Treeview(contenedor, columns=columnas, show="headings")
        for col, width in zip(columnas, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")
        scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(contenedor, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        return tree

    def seleccionar_modulo(self, nombre):
        self.tabview.set(nombre)
        for modulo, boton in self.botones_nav.items():
            boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=235, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            self.sidebar_frame,
            text="📅 AGENDA 🦆🦆🦆",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(28, 5), sticky="w")

        ctk.CTkLabel(
            self.sidebar_frame,
            text="Gestión de usuarios, categorías, ubicaciones y eventos",
            font=ctk.CTkFont(size=11),
            wraplength=190,
            justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 25), sticky="w")

        self.botones_nav = {}
        for i, (nombre, icono) in enumerate([
            ("Usuarios", "👥"),
            ("Categorías", "📁"),
            ("Eventos", "📆"),
            ("Ubicaciones", "📌"),
            ("Tareas", "✅"),
            ("Disponibilidades", "⏰")
        ], start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=f"{icono}  {nombre}",
                anchor="w", fg_color="transparent",
                command=lambda n=nombre: self.seleccionar_modulo(n)
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.botones_nav[nombre] = btn

        ctk.CTkButton(
            self.sidebar_frame,
            text="🔄 Recargar datos",
            command=self.actualizar_todas_las_tablas
        ).grid(row=8, column=0, padx=15, pady=(20, 5), sticky="ew")

        ctk.CTkLabel(self.sidebar_frame, text="APARIENCIA", font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=11, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.option_mode = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["System", "Dark", "Light"],
            command=ctk.set_appearance_mode
        )
        self.option_mode.set("System")
        self.option_mode.grid(row=12, column=0, padx=15, pady=(0, 25), sticky="ew")

    def crear_area_principal(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_container, command=self.al_cambiar_pestana)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        self.tab_usuarios = self.tabview.add("Usuarios")
        self.tab_categorias = self.tabview.add("Categorías")
        self.tab_eventos = self.tabview.add("Eventos")
        self.tab_ubicaciones = self.tabview.add("Ubicaciones")
        self.tab_tareas = self.tabview.add("Tareas")
        self.tab_disponibilidades = self.tabview.add("Disponibilidades")
        
        self.configurar_pestana_usuarios()
        self.configurar_pestana_categorias()
        self.configurar_pestana_eventos()
        self.configurar_pestana_ubicaciones()
        self.configurar_pestana_tareas()
        self.configurar_pestana_disponibilidades()
        self.seleccionar_modulo("Usuarios")

    def al_cambiar_pestana(self):
        nombre = self.tabview.get()
        if nombre in self.botones_nav:
            for modulo, boton in self.botones_nav.items():
                boton.configure(fg_color=("gray75", "gray25") if modulo == nombre else "transparent")

    def crear_encabezado(self, parent, titulo, descripcion):
        ctk.CTkLabel(parent, text=titulo, font=ctk.CTkFont(size=24, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 0)
        )
        ctk.CTkLabel(parent, text=descripcion, font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=15, pady=(0, 12)
        )

    # ---------------- DISPONIBILIDADES -----------------

    def configurar_pestana_disponibilidades(self):
        self.crear_encabezado(self.tab_disponibilidades, "Disponibilidades", "Registra, consulta y administra las tareas pertenecientes a tu evento.")

        cuerpo = ctk.CTkScrollableFrame(self.tab_disponibilidades, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(2, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tabla_frame1 = ctk.CTkFrame(cuerpo)
        tabla_frame1.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        tabla_frame2 = ctk.CTkFrame(cuerpo)
        tabla_frame2.grid(row=2, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkFrame(cuerpo, width=250)
        form.grid(row=0, column=1, sticky="nsew")

        form1 = ctk.CTkFrame(cuerpo, width=250)
        form1.grid(row=2, column=1, sticky="nsew")

        self.tree_disponibilidades = self.crear_treeview(
            tabla_frame, ("ID", "Usuario", "Estado", "Fecha Inicio", "Fecha Fin"),
            (40, 160, 120, 120, 120)
        )
        self.tree_disponibilidades.bind("<<TreeviewSelect>>", self.cargar_disponibilidad_seleccionado)

        self.crear_encabezado(tabla_frame1, "Gestión de Tiempos", "")
        self.tree_disponibilidades1 = self.crear_treeview(
            tabla_frame2, ("ID", "Nombre", "Apellido"),
            (40, 80, 80)
        )

        ctk.CTkLabel(form, text="Usuario").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_usuario = ctk.CTkComboBox(form, values=["Seleccione un usuario"], state="readonly")
        self.combo_usuario.set("Seleccione un usuario")
        self.combo_usuario.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Estado").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_estado = ctk.CTkComboBox(form, values=["Ocupado"]+["Disponible"]+["No disponible"], state="readonly")
        self.combo_estado.set("Seleccione un estado")
        self.combo_estado.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Fecha Limite").pack(anchor="w", padx=10, pady=(10, 2))
        fila_limitei = ctk.CTkFrame(form, fg_color="transparent"); fila_limitei.pack(fill="x", padx=10)
        self.fecha_limitei = self.crear_selector_fecha(fila_limitei)
        self.fecha_limitei.pack(side="left", fill="x", expand=True)
        self.hora_limitei = ctk.CTkEntry(fila_limitei, placeholder_text="HH:MM", width=75)
        self.hora_limitei.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form, text="Fecha Limite").pack(anchor="w", padx=10, pady=(10, 2))
        fila_limitef = ctk.CTkFrame(form, fg_color="transparent"); fila_limitef.pack(fill="x", padx=10)
        self.fecha_limitef = self.crear_selector_fecha(fila_limitef)
        self.fecha_limitef.pack(side="left", fill="x", expand=True)
        self.hora_limitef = ctk.CTkEntry(fila_limitef, placeholder_text="HH:MM", width=75)
        self.hora_limitef.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form1, text="Fecha Limite").pack(anchor="w", padx=10, pady=(10, 2))
        fila_busquedai = ctk.CTkFrame(form1, fg_color="transparent"); fila_busquedai.pack(fill="x", padx=10)
        self.fecha_busquedai = self.crear_selector_fecha(fila_busquedai)
        self.fecha_busquedai.pack(side="left", fill="x", expand=True)
        self.hora_busquedai = ctk.CTkEntry(fila_busquedai, placeholder_text="HH:MM", width=75)
        self.hora_busquedai.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form1, text="Fecha Limite").pack(anchor="w", padx=10, pady=(10, 2))
        fila_busquedaf = ctk.CTkFrame(form1, fg_color="transparent"); fila_busquedaf.pack(fill="x", padx=10)
        self.fecha_busquedaf = self.crear_selector_fecha(fila_busquedaf)
        self.fecha_busquedaf.pack(side="left", fill="x", expand=True)
        self.hora_busquedaf = ctk.CTkEntry(fila_busquedaf, placeholder_text="HH:MM", width=75)
        self.hora_busquedaf.pack(side="left", padx=(6, 0))
        
        ctk.CTkButton(form, text="➕ Crear disponibilidad", command=self.agregar_disponibilidad).pack(fill="x", padx=10, pady=(16, 5))
        ctk.CTkButton(form, text="💾 Actualizar disponibilidad", command=self.actualizar_disponibilidad).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_disponibilidades, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_disponibilidad, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(form1, text="🔍 Buscar", command=self.cargar_datosextra_disponibilidades).pack(fill="x", padx=10, pady=(16, 5))
        ctk.CTkButton(form1, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_disponibilidades1, fg_color="gray").pack(fill="x", padx=10, pady=5)

        self.limpiar_form_disponibilidades()
        self.limpiar_form_disponibilidades1()

    def limpiar_form_disponibilidades(self):
        self.tree_disponibilidades.selection_remove(self.tree_disponibilidades.selection())
        self.combo_estado.set("Seleccione un estado")
        self.combo_usuario.set("Seleccione un usuario")
        hoy = datetime.now()
        self.establecer_fecha(self.fecha_limitei, hoy)
        self.hora_limitei.delete(0, tk.END); self.hora_limitei.insert(0, "09:00")
        self.establecer_fecha(self.fecha_limitef, hoy)
        self.hora_limitef.delete(0, tk.END); self.hora_limitef.insert(0, "09:00")

    def limpiar_form_disponibilidades1(self):
        hoy = datetime.now()
        self.establecer_fecha(self.fecha_busquedai, hoy)
        self.hora_busquedai.delete(0, tk.END); self.hora_busquedai.insert(0, "09:00")
        self.establecer_fecha(self.fecha_busquedaf, hoy)
        self.hora_busquedaf.delete(0, tk.END); self.hora_busquedaf.insert(0, "09:00")
        for item in self.tree_disponibilidades1.get_children(): self.tree_disponibilidades1.delete(item)

    def cargar_datos_disponibilidades(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT 
                    d.id_disponibilidad, 
                    u.nombre, u.apellido, u.id_usuario, 
                    t.nombre, t.id_tipo,
                    d.fecha_inicio, d.fecha_fin
                    
                    FROM disponibilidades d
                    JOIN usuarios u ON u.id_usuario = d.usuario
                    JOIN tipos_disponibilidad t on t.id_tipo = d.estado
                    ORDER BY d.id_disponibilidad ASC
            """, fetch=True)
            for item in self.tree_disponibilidades.get_children(): self.tree_disponibilidades.delete(item)
            #self.estados_combo = {}
            for row in rows:
                usuario = f"{row[1]} {row[2]} — #{row[3]}"
                estado = f"{row[4]} — #{row[5]}"
                inicio = row[6].strftime("%Y-%m-%d %H:%M") if hasattr(row[6], "strftime") else row[6]
                fin = row[7].strftime("%Y-%m-%d %H:%M") if hasattr(row[7], "strftime") else row[7]
                self.tree_disponibilidades.insert("", "end", values=(row[0], usuario, estado, inicio, fin))
                #self.estados_combo[estado] = row[5]

            rows = self.ejecutar_consulta("""
                SELECT 
                    nombre,
                    id_tipo  
                FROM tipos_disponibilidad
            """, fetch=True)
            self.estados_combo = {}
            for row in rows:
                estado = f"{row[0]} — #{row[1]}"
                self.estados_combo[estado] = row[1]

            valores_u = ["Seleccione un usuario"] + list(self.usuarios_combo.keys())
            valores_e = ["Seleccione un estado"] + list(self.estados_combo.keys())

            self.combo_usuario.configure(values=valores_u)
            self.combo_estado.configure(values=valores_e)

        except Exception as e:
            print(f"Error cargando eventos: {e}")

    def cargar_datosextra_disponibilidades(self):
        inicio = datetime.strptime(f"{self.obtener_fecha(self.fecha_busquedai)} {self.hora_busquedai.get().strip()}", "%Y-%m-%d %H:%M")
        fin = datetime.strptime(f"{self.obtener_fecha(self.fecha_busquedaf)} {self.hora_busquedaf.get().strip()}", "%Y-%m-%d %H:%M")
        try:
            rows = self.ejecutar_consulta("""
                SELECT nombre, apellido, id_usuario
                    FROM usuarios u
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM disponibilidades d 
                        WHERE u.id_usuario = d.usuario
                            and estado != 1
                            AND d.fecha_inicio <= %s
                            AND d.fecha_fin >= %s
                    )
                    order by id_usuario ASC
            """, (fin, inicio), fetch=True)
            for item in self.tree_disponibilidades1.get_children(): self.tree_disponibilidades1.delete(item)
            for row in rows:
                self.tree_disponibilidades1.insert("", "end", values=(row[2], row[0], row[1]))
        except Exception as e:
            print(f"Error cargando eventos: {e}")

    def cargar_disponibilidad_seleccionado(self, _=None):
        sel = self.tree_disponibilidades.selection()
        if not sel: return
        vals = self.tree_disponibilidades.item(sel[0])["values"]
        self.combo_usuario.set(vals[1])
        self.combo_estado.set(vals[2])
        try:
            limite = datetime.strptime(str(vals[3]), "%Y-%m-%d %H:%M")
            self.establecer_fecha(self.fecha_limitei, limite)
            self.hora_limitei.delete(0, tk.END); self.hora_limitei.insert(0, limite.strftime("%H:%M"))

            limite1 = datetime.strptime(str(vals[4]), "%Y-%m-%d %H:%M")
            self.establecer_fecha(self.fecha_limitef, limite1)
            self.hora_limitef.delete(0, tk.END); self.hora_limitef.insert(0, limite1.strftime("%H:%M"))
        except ValueError:
            pass

    def datos_disponibilidad_formulario(self):
            usuario = self.usuarios_combo.get(self.combo_usuario.get())
            estado = self.estados_combo.get(self.combo_estado.get())
            try:
                limite = datetime.strptime(f"{self.obtener_fecha(self.fecha_limitei)} {self.hora_limitei.get().strip()}", "%Y-%m-%d %H:%M")
                limite1 = datetime.strptime(f"{self.obtener_fecha(self.fecha_limitef)} {self.hora_limitef.get().strip()}", "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError("La hora debe tener formato HH:MM, por ejemplo 09:30.")
            if usuario is None or estado is None:
                raise ValueError("Completa título, propietario y categoría.")
            if limite1 <= limite:
                raise ValueError("La fecha y hora de finalización deben ser posteriores al inicio.")
            return usuario, estado, limite, limite1
    
    def agregar_disponibilidad(self):
        try:
            datos = self.datos_disponibilidad_formulario()
            self.ejecutar_consulta("""
                INSERT INTO disponibilidades (usuario, estado, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s);        
                """, datos)
            self.limpiar_form_disponibilidades(); self.cargar_datos_disponibilidades()
            messagebox.showinfo("Éxito", "Disponibilidad creada correctamente.")
        except Exception as e:
            messagebox.showerror("No se pudo crear la disponibilidad", str(e))

    def disponibilidad_seleccionada_id(self):
        sel = self.tree_disponibilidades.selection()
        return self.tree_disponibilidades.item(sel[0])["values"][0] if sel else None

    def eliminar_disponibilidad(self):
            uid = self.disponibilidad_seleccionada_id()
            if uid is None:
                return messagebox.showwarning("Selección requerida", "Selecciona una tarea.")
            if not messagebox.askyesno("Confirmar", "¿Eliminar la disponibilidad seleccionada?"):
                return
            try:
                self.ejecutar_consulta("DELETE FROM disponibilidades WHERE id_disponibilidad=%s", (uid,))
                self.limpiar_form_disponibilidades(); self.actualizar_todas_las_tablas()
                messagebox.showinfo("Eliminada", "Disponibilidad eliminada.")
            except Exception as e:
                messagebox.showerror("No se pudo eliminar", str(e))     

    def actualizar_disponibilidad(self):
        eid = self.disponibilidad_seleccionada_id()
        if eid is None: return messagebox.showwarning("Selección requerida", "Selecciona una tarea.")
        try:
            usuario, estado, inicio, fin = self.datos_disponibilidad_formulario()
            self.ejecutar_consulta("""
                UPDATE disponibilidades SET 
                usuario =%s, 
                estado =%s, 
                fecha_inicio =%s, 
                fecha_fin =%s
                WHERE id_disponibilidad=%s
            """, (usuario, estado, inicio, fin, eid))
            self.cargar_datos_disponibilidades(); messagebox.showinfo("Éxito", "Tarea actualizada.")
        except Exception as e:
            messagebox.showerror("No se pudo actualizar", str(e))

    # -------------------- TAREAS -----------------

    def configurar_pestana_ubicaciones(self):
        self.crear_encabezado(self.tab_tareas, "Tareas", "Registra, consulta y administra las tareas pertenecientes a tu evento.")

        cuerpo = ctk.CTkScrollableFrame(self.tab_tareas, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(1, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tabla_frame1 = ctk.CTkFrame(cuerpo)
        tabla_frame1.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        form = ctk.CTkFrame(cuerpo, width=350)
        form.grid(row=0, column=1, rowspan=2, sticky="nsew")

        self.tree_tareas = self.crear_treeview(
            tabla_frame, ("ID", "Evento", "Responsable", "Titulo", "Fecha Limite", "Prioridad", "Estado"),
            (40, 100, 160, 80, 120, 80, 80)
        )
        self.tree_tareas.bind("<<TreeviewSelect>>", self.cargar_tarea_seleccionado)

        self.crear_encabezado(tabla_frame1, "Reporte de Carga de Trabajo", "")
        self.tree_tareas1 = self.crear_treeview(
            tabla_frame1, ("Responsable", "Pendientes", "Iniciadas", "Vencidas"),
            (160, 80, 80, 80)
        )

        ctk.CTkLabel(form, text="Formulario de tarea", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))

        self.entry_titulo = ctk.CTkEntry(form, placeholder_text="Titulo")
        self.entry_titulo.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Evento").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_evento = ctk.CTkComboBox(form, values=["Seleccione un evento"], state="readonly")
        self.combo_ev_evento.set("Seleccione un evento")
        self.combo_ev_evento.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Responsable").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_resposable = ctk.CTkComboBox(form, values=["Seleccione un responsable"], state="readonly")
        self.combo_ev_resposable.set("Seleccione un responsable")
        self.combo_ev_resposable.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Prioridad").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_prioridad = ctk.CTkComboBox(form, values=["Baja"]+["Media"]+["Alta"], state="readonly")
        self.combo_ev_prioridad.set("Seleccione la prioridad")
        self.combo_ev_prioridad.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Estado").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_estado = ctk.CTkComboBox(form, values=["Pendiente"]+["En progreso"]+["Completada"]+["Cancelada"], state="readonly")
        self.combo_ev_estado.set("Seleccione el estado")
        self.combo_ev_estado.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Fecha Limite").pack(anchor="w", padx=10, pady=(10, 2))
        fila_limite = ctk.CTkFrame(form, fg_color="transparent"); fila_limite.pack(fill="x", padx=10)
        self.fecha_limite = self.crear_selector_fecha(fila_limite)
        self.fecha_limite.pack(side="left", fill="x", expand=True)
        self.hora_limite = ctk.CTkEntry(fila_limite, placeholder_text="HH:MM", width=75)
        self.hora_limite.pack(side="left", padx=(6, 0))

        ctk.CTkButton(form, text="➕ Crear evento", command=self.agregar_tarea).pack(fill="x", padx=10, pady=(16, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_tarea).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_tareas, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_tarea, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

        self.limpiar_form_tareas()

    def limpiar_form_tareas(self):
        self.tree_tareas.selection_remove(self.tree_tareas.selection())
        self.entry_titulo.delete(0, tk.END)
        self.combo_ev_evento.set("Seleccione un evento")
        self.combo_ev_resposable.set("Seleccione un responsable")
        self.combo_ev_prioridad.set("Seleccione la prioridad")
        self.combo_ev_estado.set("Seleccione el estado")
        hoy = datetime.now()
        self.establecer_fecha(self.fecha_limite, hoy)
        self.hora_limite.delete(0, tk.END); self.hora_limite.insert(0, "09:00")

    def cargar_tarea_seleccionado(self, _=None):
        sel = self.tree_tareas.selection()
        if not sel: return
        vals = self.tree_tareas.item(sel[0])["values"]
        self.entry_titulo.delete(0, tk.END); self.entry_titulo.insert(0, vals[3])
        self.combo_ev_evento.set(vals[1])
        self.combo_ev_resposable.set(vals[2])
        self.combo_ev_prioridad.set(vals[5])
        self.combo_ev_estado.set(vals[6])
        try:
            limite = datetime.strptime(str(vals[4]), "%Y-%m-%d %H:%M")
            self.establecer_fecha(self.fecha_limite, limite)
            self.hora_limite.delete(0, tk.END); self.hora_limite.insert(0, limite.strftime("%H:%M"))
        except ValueError:
            pass

    def cargar_datos_tareas(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT 
                    t.id_tarea, 
                    e.id_evento, e.titulo, 
                    u.id_usuario, u.nombre, u.apellido, 
                    t.titulo, t.descripcion, t.fecha_limite, t.prioridad, t.estado 

                    FROM tareas t
                    JOIN usuarios u ON u.id_usuario = t.responsable 
                    JOIN eventos e on e.id_evento = t.id_evento  
                    ORDER BY t.id_evento  DESC
            """, fetch=True)
            for item in self.tree_tareas.get_children(): self.tree_tareas.delete(item)
            for row in rows:
                usuario = f"{row[4]} {row[5]} — #{row[3]}"
                evento = f"{row[2]} — #{row[1]}"
                limite = row[8].strftime("%Y-%m-%d %H:%M") if hasattr(row[8], "strftime") else row[8]
                self.tree_tareas.insert("", "end", values=(row[0], evento, usuario, row[6], limite, row[9], row[10]))

            valores_u = ["Seleccione un responsable"] + list(self.usuarios_combo.keys())
            valores_e = ["Seleccione un evento"] + list(self.eventos_combo.keys())

            self.combo_ev_resposable.configure(values=valores_u)
            self.combo_ev_evento.configure(values=valores_e)

        except Exception as e:
            print(f"Error cargando eventos: {e}")

    def tarea_seleccionada_id(self):
        sel = self.tree_tareas.selection()
        return self.tree_tareas.item(sel[0])["values"][0] if sel else None

    def eliminar_tarea(self):
            uid = self.tarea_seleccionada_id()
            if uid is None:
                return messagebox.showwarning("Selección requerida", "Selecciona una tarea.")
            if not messagebox.askyesno("Confirmar", "¿Eliminar la tarea seleccionada?"):
                return
            try:
                self.ejecutar_consulta("DELETE FROM tareas WHERE id_tarea=%s", (uid,))
                self.limpiar_form_tareas(); self.actualizar_todas_las_tablas()
                messagebox.showinfo("Eliminada", "Tarea eliminada.")
            except Exception as e:
                messagebox.showerror("No se pudo eliminar", str(e))

    def datos_tarea_formulario(self):
            titulo = self.entry_titulo.get().strip()
            usuario = self.usuarios_combo.get(self.combo_ev_resposable.get())
            evento = self.eventos_combo.get(self.combo_ev_evento.get())
            prioridad = self.combo_ev_prioridad.get().strip();
            estado = self.combo_ev_estado.get().strip();
            
            try:
                limite = datetime.strptime(f"{self.obtener_fecha(self.fecha_limite)} {self.hora_limite.get().strip()}", "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError("La hora debe tener formato HH:MM, por ejemplo 09:30.")
            if not titulo or usuario is None or evento is None:
                raise ValueError("Completa título, propietario y categoría.")
            return evento, usuario, titulo, limite, prioridad, estado
    
    def agregar_tarea(self):
        try:
            datos = self.datos_tarea_formulario()
            self.ejecutar_consulta("""
                INSERT INTO tareas(id_evento, responsable, titulo, descripcion, fecha_limite, prioridad, estado) 
                VALUES (%s, %s, %s, null, %s, %s, %s);        
                """, datos)
            self.limpiar_form_tareas(); self.cargar_datos_tareas()
            messagebox.showinfo("Éxito", "Evento creado correctamente.")
        except Exception as e:
            messagebox.showerror("No se pudo crear el evento", str(e))

    def actualizar_tarea(self):
        eid = self.tarea_seleccionada_id()
        if eid is None: return messagebox.showwarning("Selección requerida", "Selecciona una tarea.")
        try:
            evento, usuario, titulo, limite, prioridad, estado = self.datos_tarea_formulario()
            self.ejecutar_consulta("""
                UPDATE tareas SET 
                id_evento=%s,
                responsable=%s, 
                titulo=%s,
                fecha_limite=%s, 
                prioridad=%s, 
                estado=%s 
                WHERE id_tarea=%s
            """, (evento, usuario, titulo, limite, prioridad, estado, eid))
            self.cargar_datos_tareas(); messagebox.showinfo("Éxito", "Tarea actualizada.")
        except Exception as e:
            messagebox.showerror("No se pudo actualizar", str(e))
        
    def cargar_reporte_tareas(self):
        try:
            rows = self.ejecutar_consulta("""
                select 
                    u.nombre,
                    u.apellido,
                    u.id_usuario,
                    COUNT(*) FILTER (WHERE t.estado = 'Pendiente'), 
                    COUNT(*) FILTER (WHERE t.estado = 'En progreso'), 
                    COUNT(*) FILTER (WHERE t.fecha_limite < CURRENT_DATE)
                from tareas t, usuarios u
                where t.responsable = u.id_usuario
                group by u.id_usuario
            """,fetch=True)
            for item in self.tree_tareas1.get_children(): self.tree_tareas1.delete(item)
            for row in rows:
                usuario = f"{row[0]} {row[1]} — #{row[2]}"
                self.tree_tareas1.insert("", "end", values=(usuario, row[3], row[4], row[5]))  
        except Exception as e:
            print(f"Error cargando Ubicaciones: {e}")

    # -------------------- UBICACIONES -----------------

    def configurar_pestana_tareas(self):
        # Crea el encabezado
        self.crear_encabezado(self.tab_ubicaciones, "Ubicaciones", "Registra, consulta y administra las ubicaciones para tus eventos.")

        # Crea una tabla y se definen las filas y columnas. Se expanden al tamaño de la pantalla
        cuerpo = ctk.CTkScrollableFrame(self.tab_ubicaciones, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)

        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_columnconfigure(2, weight=1)
        cuerpo.grid_columnconfigure(3, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(2, weight=1)

        # Crea la seccion donde iran los botones y los campos de texto
        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=(0, 8))

        tabla_frame1 = ctk.CTkFrame(cuerpo)
        tabla_frame1.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        tabla_frame2 = ctk.CTkFrame(cuerpo)
        tabla_frame2.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=(0, 8))

        tabla_frame3 = ctk.CTkFrame(cuerpo)
        tabla_frame3.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 8))

        tabla_frame4= ctk.CTkFrame(cuerpo)
        tabla_frame4.grid(row=2, column=2, columnspan=2, sticky="nsew", padx=(0, 8))

        self.crear_encabezado(tabla_frame3, "Recintos más solicitados", "")
        self.crear_encabezado(tabla_frame4, "Mayor volumen de eventos", "")

        form = ctk.CTkFrame(cuerpo, width=250)
        form.grid(row=0, column=3, rowspan=2, sticky="nsew")


        # Crea la tabla donde se visualizan los datos
        self.tree_ubicaciones = self.crear_treeview(
            tabla_frame, ("ID", "Nombre", "Direccion", "Ciudad", "Capacidad"),
            (40, 80, 160, 80, 40)
        )
        self.tree_ubicaciones.bind("<<TreeviewSelect>>", self.cargar_ubicacion_seleccionada)
        self.tree_ubicaciones_historicas = self.crear_treeview(
            tabla_frame1, ("Historial", "Tiempo transcurrido"),
            (140,140)
        )
        self.tree_ubicaciones_actuales = self.crear_treeview(
            tabla_frame2, ("Proximos Eventos", "Inicio", "Fin"),
            (140, 140, 140)
        )
        self.tree_reporte1 = self.crear_treeview(
            tabla_frame3, ("Nombre", "Cantidad de eventos"),
            (140, 140)
        )
        self.tree_reporte2 = self.crear_treeview(
            tabla_frame4, ("Nombre", "Total de visitantes"),
            (140, 140)
        )

        # Cuadros de texto
        ctk.CTkLabel(form, text="Formulario de ubicación", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_nombreubi = ctk.CTkEntry(form, placeholder_text="Nombre")
        self.entry_nombreubi.pack(fill="x", padx=10, pady=6)
        self.entry_direccion = ctk.CTkEntry(form, placeholder_text="Direccion")
        self.entry_direccion.pack(fill="x", padx=10, pady=6)
        self.entry_ciudad = ctk.CTkEntry(form, placeholder_text="Ciudad")
        self.entry_ciudad.pack(fill="x", padx=10, pady=6)
        self.entry_capacidad = ctk.CTkEntry(form, placeholder_text="Capacidad")
        self.entry_capacidad.pack(fill="x", padx=10, pady=6)

        # Botones
        ctk.CTkButton(form, text="➕ Registrar ubicación", command=self.agregar_ubicacion).pack(fill="x", padx=10, pady=(12, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_ubicacion).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_ubicaciones, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_ubicacion, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def cargar_ubicacion_seleccionada(self, _=None):
        sel = self.tree_ubicaciones.selection()
        if not sel:
            return
        vals = self.tree_ubicaciones.item(sel[0])["values"]
        self.cargar_datosextra_ubicaciones(vals[0])
        self.entry_nombreubi.delete(0, tk.END); self.entry_nombreubi.insert(0, vals[1])
        self.entry_direccion.delete(0, tk.END); self.entry_direccion.insert(0, vals[2])
        self.entry_ciudad.delete(0, tk.END); self.entry_ciudad.insert(0, vals[3])
        self.entry_capacidad.delete(0, tk.END); self.entry_capacidad.insert(0, vals[4])

    def cargar_datosextra_ubicaciones(self, id):
        try:
            rows = self.ejecutar_consulta(
                "SELECT titulo, date_trunc('second', fecha_fin - NOW()) FROM eventos where id_ubicacion = %s and fecha_fin < NOW() order by fecha_inicio desc", (id,),
                fetch=True
            )
            for item in self.tree_ubicaciones_historicas.get_children(): self.tree_ubicaciones_historicas.delete(item)
            for row in rows:
                self.tree_ubicaciones_historicas.insert("", "end", values=(row[0], row[1]))
                
        except Exception as e:
            print(f"Error cargando Ubicaciones: {e}")
            
        try:
            rows = self.ejecutar_consulta(
                "SELECT titulo, fecha_inicio , fecha_fin FROM eventos where id_ubicacion = %s and fecha_inicio > NOW() order by fecha_inicio asc", (id,),
                fetch=True
            )
            for item in self.tree_ubicaciones_actuales.get_children(): self.tree_ubicaciones_actuales.delete(item)
            for row in rows:
                self.tree_ubicaciones_actuales.insert("", "end", values=(row[0], row[1], row[2]))
                
        except Exception as e:
            print(f"Error cargando Ubicaciones: {e}")

    def cargar_datos_ubicaciones(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT id_ubicacion, nombre, direccion, ciudad, capacidad FROM ubicaciones order by nombre",
                fetch=True
            )
            for item in self.tree_ubicaciones.get_children(): self.tree_ubicaciones.delete(item)
            self.ubicaciones_combo = {}
            for row in rows:
                self.tree_ubicaciones.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4]))
                etiqueta = f"{row[1]} — #{row[0]}"
                self.ubicaciones_combo[etiqueta] = row[0]
                
        except Exception as e:
            print(f"Error cargando Ubicaciones: {e}")

    def limpiar_form_ubicaciones(self):
        self.tree_ubicaciones.selection_remove(self.tree_ubicaciones.selection())
        self.entry_nombreubi.delete(0, tk.END)
        self.entry_direccion.delete(0, tk.END)    
        self.entry_ciudad.delete(0, tk.END)
        self.entry_capacidad.delete(0, tk.END)

    def agregar_ubicacion(self):
        nombre = self.entry_nombreubi.get()
        direccion = self.entry_direccion.get()
        ciudad = self.entry_ciudad.get()
        capacidad = self.entry_capacidad.get()

        if not nombre or not direccion or not ciudad or not capacidad:
            return messagebox.showwarning("Campos incompletos", "Indica nombre, direccion, ciudad y capacidad.")
        try:
            self.ejecutar_consulta("INSERT INTO ubicaciones (nombre, direccion, ciudad, capacidad) VALUES (%s, %s, %s, %s)",
                                   (nombre, direccion, ciudad, capacidad))
            self.limpiar_form_ubicaciones(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Ubicacion registrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def ubicacion_seleccionada_id(self):
        sel = self.tree_ubicaciones.selection()
        return self.tree_ubicaciones.item(sel[0])["values"][0] if sel else None
    
    def actualizar_ubicacion(self):
        uid = self.ubicacion_seleccionada_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona una ubicacion para actualizar.")
        nombre = self.entry_nombreubi.get()
        direccion = self.entry_direccion.get()
        ciudad = self.entry_ciudad.get()
        capacidad = self.entry_capacidad.get()
        if not nombre or not direccion or not ciudad or not capacidad:
            return messagebox.showwarning("Campos incompletos", "Indica nombre, direccion, ciudad y capacidad.")
        try:
            self.ejecutar_consulta("UPDATE ubicaciones SET nombre=%s, direccion=%s, ciudad=%s, capacidad=%s WHERE id_ubicacion=%s",
                                    (nombre, direccion, ciudad, capacidad, uid))
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Ubicacion actualizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_ubicacion(self):
        uid = self.ubicacion_seleccionada_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un ubicacion para eliminar.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar la ubicacion seleccionada?"):
            return
        try:
            self.ejecutar_consulta("DELETE FROM ubicaciones WHERE id_ubicacion=%s", (uid,))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Ubicacion eliminada.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_reportes(self):
        try:
            rows = self.ejecutar_consulta("""
                select e.id_ubicacion, u.nombre, count(e.id_evento) as cantidad
                from eventos e, ubicaciones u
                where e.id_ubicacion = u.id_ubicacion
                group by e.id_ubicacion, u.nombre
                order by cantidad desc
            """,fetch=True)
            for item in self.tree_reporte1.get_children(): self.tree_reporte1.delete(item)
            for row in rows:
                self.tree_reporte1.insert("", "end", values=(row[1], row[2]))  
        except Exception as e:
            print(f"Error cargando Ubicaciones: {e}")

        try:
            rows = self.ejecutar_consulta("""
                select e.id_ubicacion, u.nombre, SUM(u.capacidad) as personas
                from eventos e, ubicaciones u
                where e.id_ubicacion = u.id_ubicacion
                group by e.id_ubicacion, u.nombre
                order by personas desc
            """,fetch=True)
            for item in self.tree_reporte2.get_children(): self.tree_reporte2.delete(item)
            for row in rows:
                self.tree_reporte2.insert("", "end", values=(row[1], row[2]))  
        except Exception as e:
            print(f"Error cargando Ubicaciones: {e}")

    # -------------------- USUARIOS --------------------

    def configurar_pestana_usuarios(self):
        self.crear_encabezado(self.tab_usuarios, "Usuarios", "Registra, consulta y administra los usuarios de la agenda.")

        cuerpo = ctk.CTkFrame(self.tab_usuarios, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1)
        #los pesos de las filas estan invertidos?
        cuerpo.grid_rowconfigure(0, weight=3)
        cuerpo.grid_rowconfigure(1, weight=1)

        tabla_frame = ctk.CTkFrame(cuerpo)
        tabla_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tabla_frame1 = ctk.CTkFrame(cuerpo)
        tabla_frame1.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=300)
        form.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 15))

        self.tree_usuarios = self.crear_treeview(
            tabla_frame, ("ID", "Nombre", "Apellido", "Registro", "Activo"),
            (50, 160, 160, 160, 80)
        )
        self.tree_usuarios.bind("<<TreeviewSelect>>", self.cargar_usuario_seleccionado)

        self.tree_usuarios_tareas = self.crear_treeview(
            tabla_frame1, ("ID", "Tarea Pendiente", "Tiempo restante", "Prioridad"),
            (40, 200, 80, 40)
        )

        ctk.CTkLabel(form, text="Formulario de usuario", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre")
        self.entry_nombre.pack(fill="x", padx=10, pady=6)
        self.entry_apellido = ctk.CTkEntry(form, placeholder_text="Apellido")
        self.entry_apellido.pack(fill="x", padx=10, pady=6)

        self.switch_usuario_activo = ctk.CTkSwitch(form, text="Usuario activo")
        self.switch_usuario_activo.select()
        self.switch_usuario_activo.pack(anchor="w", padx=12, pady=10)

        ctk.CTkButton(form, text="➕ Registrar usuario", command=self.agregar_usuario).pack(fill="x", padx=10, pady=(12, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_usuario).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_usuario, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_usuario, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def usuario_seleccionado_id(self):
        sel = self.tree_usuarios.selection()
        return self.tree_usuarios.item(sel[0])["values"][0] if sel else None

    def cargar_usuario_seleccionado(self, _=None):
        sel = self.tree_usuarios.selection()
        if not sel:
            return
        vals = self.tree_usuarios.item(sel[0])["values"]
        self.cargar_datosextra_usuarios(vals[0])
        self.entry_nombre.delete(0, tk.END); self.entry_nombre.insert(0, vals[1])
        self.entry_apellido.delete(0, tk.END); self.entry_apellido.insert(0, vals[2])
        if vals[4]:
            self.switch_usuario_activo.select()
        else:
            self.switch_usuario_activo.deselect()

    def cargar_datosextra_usuarios(self, id):
        try:
            rows = self.ejecutar_consulta(
                "SELECT id_tarea, descripcion, date_trunc('second', fecha_limite - NOW()), prioridad FROM tareas where responsable = %s AND NOW()::timestamp < fecha_limite order by fecha_limite desc", (id,),
                fetch=True
            )
            for item in self.tree_usuarios_tareas.get_children(): self.tree_usuarios_tareas.delete(item)
            for row in rows:
                self.tree_usuarios_tareas.insert("", "end", values=(row[0], row[1], row[2], row[3]))
                
        except Exception as e:
            print(f"Error cargando Ubicaciones: {e}")

    def limpiar_form_usuario(self):
        self.tree_usuarios.selection_remove(self.tree_usuarios.selection())
        self.entry_nombre.delete(0, tk.END)
        self.entry_apellido.delete(0, tk.END)
        self.switch_usuario_activo.select()

    def agregar_usuario(self):
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("INSERT INTO usuarios (nombre, apellido, activo) VALUES (%s, %s, %s)",
                                   (nombre, apellido, self.switch_usuario_activo.get() == 1))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
        except Exception as e:
            messagebox.showerror("Error de base de datos", str(e))

    def actualizar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario para actualizar.")
        nombre, apellido = self.entry_nombre.get().strip(), self.entry_apellido.get().strip()
        if not nombre or not apellido:
            return messagebox.showwarning("Campos incompletos", "Indica nombre y apellido.")
        try:
            self.ejecutar_consulta("UPDATE usuarios SET nombre=%s, apellido=%s, activo=%s WHERE id_usuario=%s",
                                   (nombre, apellido, self.switch_usuario_activo.get() == 1, uid))
            self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Usuario actualizado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_usuario(self):
        uid = self.usuario_seleccionado_id()
        if uid is None:
            return messagebox.showwarning("Selección requerida", "Selecciona un usuario.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el usuario seleccionado?"):
            return
        try:
            self.ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=%s", (uid,))
            self.limpiar_form_usuario(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Usuario eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_usuarios(self):
        try:
            rows = self.ejecutar_consulta(
                "SELECT id_usuario, nombre, apellido, fecha_registro, activo FROM usuarios ORDER BY nombre, apellido",
                fetch=True
            )
            for item in self.tree_usuarios.get_children(): self.tree_usuarios.delete(item)
            self.usuarios_combo = {}
            for row in rows:
                registro = row[3].strftime("%Y-%m-%d %H:%M") if hasattr(row[3], "strftime") else row[3]
                self.tree_usuarios.insert("", "end", values=(row[0], row[1], row[2], registro, "Sí" if row[4] else "No"))
                etiqueta = f"{row[1]} {row[2]} — #{row[0]}"
                self.usuarios_combo[etiqueta] = row[0]
        except Exception as e:
            print(f"Error cargando usuarios: {e}")

    # -------------------- CATEGORÍAS --------------------

    def configurar_pestana_categorias(self):
        self.crear_encabezado(self.tab_categorias, "Categorías", "Organiza los eventos mediante categorías y subcategorías.")

        cuerpo = ctk.CTkFrame(self.tab_categorias, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3); cuerpo.grid_columnconfigure(1, weight=1); cuerpo.grid_rowconfigure(0, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=320); form.grid(row=0, column=1, sticky="nsew")

        self.tree_categorias = self.crear_treeview(tabla, ("ID", "Categoría", "Categoría padre"), (80, 230, 230))
        self.tree_categorias.bind("<<TreeviewSelect>>", self.cargar_categoria_seleccionada)

        ctk.CTkLabel(form, text="Formulario de categoría", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15))
        self.entry_cat_nombre = ctk.CTkEntry(form, placeholder_text="Nombre de la categoría")
        self.entry_cat_nombre.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(form, text="Categoría padre").pack(anchor="w", padx=10, pady=(10, 2))
        self.combo_cat_padre = ctk.CTkComboBox(form, values=["Sin categoría padre"], state="readonly")
        self.combo_cat_padre.set("Sin categoría padre")
        self.combo_cat_padre.pack(fill="x", padx=10, pady=6)

        ctk.CTkButton(form, text="➕ Crear categoría", command=self.agregar_categoria).pack(fill="x", padx=10, pady=(15, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionada", command=self.actualizar_categoria).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nueva / Limpiar", command=self.limpiar_form_categoria, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionada", command=self.eliminar_categoria, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

    def categoria_seleccionada_id(self):
        sel = self.tree_categorias.selection()
        return self.tree_categorias.item(sel[0])["values"][0] if sel else None

    def cargar_categoria_seleccionada(self, _=None):
        sel = self.tree_categorias.selection()
        if not sel: return
        vals = self.tree_categorias.item(sel[0])["values"]
        self.entry_cat_nombre.delete(0, tk.END); self.entry_cat_nombre.insert(0, vals[1])
        padre = vals[2]
        self.combo_cat_padre.set(padre if padre in self.categorias_padre_combo else "Sin categoría padre")

    def limpiar_form_categoria(self):
        self.tree_categorias.selection_remove(self.tree_categorias.selection())
        self.entry_cat_nombre.delete(0, tk.END); self.combo_cat_padre.set("Sin categoría padre")

    def _padre_id_actual(self):
        valor = self.combo_cat_padre.get()
        return None if valor == "Sin categoría padre" else self.categorias_padre_combo.get(valor)

    def agregar_categoria(self):
        nombre = self.entry_cat_nombre.get().strip()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre de la categoría.")
        try:
            self.ejecutar_consulta("INSERT INTO categorias (nombre, id_categoria_padre) VALUES (%s, %s)",
                                   (nombre, self._padre_id_actual()))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Éxito", "Categoría creada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        nombre = self.entry_cat_nombre.get().strip(); padre = self._padre_id_actual()
        if not nombre: return messagebox.showwarning("Campo requerido", "Indica el nombre.")
        if padre == cid: return messagebox.showwarning("Relación inválida", "Una categoría no puede ser su propia categoría padre.")
        try:
            self.ejecutar_consulta("UPDATE categorias SET nombre=%s, id_categoria_padre=%s WHERE id_categoria=%s",
                                   (nombre, padre, cid))
            self.actualizar_todas_las_tablas(); messagebox.showinfo("Éxito", "Categoría actualizada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_categoria(self):
        cid = self.categoria_seleccionada_id()
        if cid is None: return messagebox.showwarning("Selección requerida", "Selecciona una categoría.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar la categoría seleccionada?"): return
        try:
            self.ejecutar_consulta("DELETE FROM categorias WHERE id_categoria=%s", (cid,))
            self.limpiar_form_categoria(); self.actualizar_todas_las_tablas()
            messagebox.showinfo("Eliminado", "Categoría eliminada.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_categorias(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT c.id_categoria, c.nombre, p.nombre
                FROM categorias c
                LEFT JOIN categorias p ON p.id_categoria = c.id_categoria_padre
                ORDER BY c.nombre
            """, fetch=True)
            ids = self.ejecutar_consulta("SELECT id_categoria, nombre FROM categorias ORDER BY nombre", fetch=True)

            for item in self.tree_categorias.get_children(): self.tree_categorias.delete(item)
            self.categorias_combo = {}
            self.categorias_padre_combo = {}
            for cid, nombre in ids:
                etiqueta = f"{nombre} — #{cid}"
                self.categorias_combo[etiqueta] = cid
                self.categorias_padre_combo[etiqueta] = cid
            for row in rows:
                padre = "Sin categoría padre"
                if row[2] is not None:
                    # Buscar etiqueta completa del padre
                    for etiqueta, cid in self.categorias_padre_combo.items():
                        if etiqueta.startswith(f"{row[2]} —"):
                            padre = etiqueta; break
                self.tree_categorias.insert("", "end", values=(row[0], row[1], padre))

            valores_padre = ["Sin categoría padre"] + list(self.categorias_padre_combo.keys())
            self.combo_cat_padre.configure(values=valores_padre)
            if self.combo_cat_padre.get() not in valores_padre:
                self.combo_cat_padre.set("Sin categoría padre")
        except Exception as e:
            print(f"Error cargando categorías: {e}")

    # -------------------- EVENTOS --------------------

    def configurar_pestana_eventos(self):
        self.crear_encabezado(self.tab_eventos, "Eventos", "Programa eventos seleccionando usuarios, categorías, fechas y horas.")

        cuerpo = ctk.CTkFrame(self.tab_eventos, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=5)
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=1) 
        cuerpo.grid_rowconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(1, weight=1)

        tabla = ctk.CTkFrame(cuerpo); tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tabla1 = ctk.CTkFrame(cuerpo); tabla1.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        form = ctk.CTkScrollableFrame(cuerpo, width=350); form.grid(row=0, column=1, rowspan=2, sticky="nsew")

        self.tree_eventos = self.crear_treeview(
            tabla, ("ID", "Propietario", "Categoría", "Título", "Ubicacion", "Inicio", "Fin"),
            (70, 170, 150, 150, 150, 150, 150)
        )
        self.tree_eventos.bind("<<TreeviewSelect>>", self.cargar_evento_seleccionado)

        self.tree_eventos_tareas = self.crear_treeview(
            tabla1, ("ID", "Tarea Vencida", "Tiempo sobrepasado", "Prioridad"),
            (40, 160, 80, 40)
        )

        ctk.CTkLabel(form, text="Formulario de evento", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 12))

        self.entry_ev_titulo = ctk.CTkEntry(form, placeholder_text="Título del evento")
        self.entry_ev_titulo.pack(fill="x", padx=10, pady=6)
        
        ctk.CTkLabel(form, text="Propietario").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_usuario = ctk.CTkComboBox(form, values=["Seleccione un usuario"], state="readonly")
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_usuario.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Categoría").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_categoria = ctk.CTkComboBox(form, values=["Seleccione una categoría"], state="readonly")
        self.combo_ev_categoria.set("Seleccione una categoría")
        self.combo_ev_categoria.pack(fill="x", padx=10, pady=4)
    
        ctk.CTkLabel(form, text="Ubicación").pack(anchor="w", padx=10, pady=(8, 2))
        self.combo_ev_ubicacion = ctk.CTkComboBox(form, values=["Seleccione una ubicación"], state="readonly")
        self.combo_ev_ubicacion.set("Seleccione una ubicación")
        self.combo_ev_ubicacion.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(form, text="Inicio").pack(anchor="w", padx=10, pady=(10, 2))
        fila_inicio = ctk.CTkFrame(form, fg_color="transparent"); fila_inicio.pack(fill="x", padx=10)
        self.fecha_inicio = self.crear_selector_fecha(fila_inicio)
        self.fecha_inicio.pack(side="left", fill="x", expand=True)
        self.hora_inicio = ctk.CTkEntry(fila_inicio, placeholder_text="HH:MM", width=75)
        self.hora_inicio.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(form, text="Fin").pack(anchor="w", padx=10, pady=(10, 2))
        fila_fin = ctk.CTkFrame(form, fg_color="transparent"); fila_fin.pack(fill="x", padx=10)
        self.fecha_fin = self.crear_selector_fecha(fila_fin)
        self.fecha_fin.pack(side="left", fill="x", expand=True)
        self.hora_fin = ctk.CTkEntry(fila_fin, placeholder_text="HH:MM", width=75)
        self.hora_fin.pack(side="left", padx=(6, 0))

        ctk.CTkButton(form, text="➕ Crear evento", command=self.agregar_evento).pack(fill="x", padx=10, pady=(16, 5))
        ctk.CTkButton(form, text="💾 Actualizar seleccionado", command=self.actualizar_evento).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🧹 Nuevo / Limpiar", command=self.limpiar_form_evento, fg_color="gray").pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(form, text="🗑️ Eliminar seleccionado", command=self.eliminar_evento, fg_color="#b33939", hover_color="#8f2d2d").pack(fill="x", padx=10, pady=5)

        self.limpiar_form_evento()

    def crear_selector_fecha(self, parent):
        if DateEntry is not None:
            return DateEntry(parent, date_pattern="yyyy-mm-dd", font=("Arial", 10))
        return ttk.Entry(parent)

    def obtener_fecha(self, widget):
        if DateEntry is not None:
            return widget.get_date().strftime("%Y-%m-%d")
        return widget.get().strip()

    def establecer_fecha(self, widget, valor):
        fecha = valor.date() if hasattr(valor, "date") else datetime.strptime(str(valor)[:10], "%Y-%m-%d").date()
        if DateEntry is not None:
            widget.set_date(fecha)
        else:
            widget.delete(0, tk.END); widget.insert(0, fecha.strftime("%Y-%m-%d"))

    def evento_seleccionado_id(self):
        sel = self.tree_eventos.selection()
        return self.tree_eventos.item(sel[0])["values"][0] if sel else None

    def cargar_evento_seleccionado(self, _=None):
        sel = self.tree_eventos.selection()
        if not sel: return
        vals = self.tree_eventos.item(sel[0])["values"]
        self.cargar_datosextra_eventos(vals[0])
        self.entry_ev_titulo.delete(0, tk.END); self.entry_ev_titulo.insert(0, vals[3])
        self.combo_ev_usuario.set(vals[1])
        self.combo_ev_categoria.set(vals[2])
        self.combo_ev_ubicacion.set(vals[4])
        try:
            ini = datetime.strptime(str(vals[5]), "%Y-%m-%d %H:%M")
            fin = datetime.strptime(str(vals[6]), "%Y-%m-%d %H:%M")
            self.establecer_fecha(self.fecha_inicio, ini)
            self.establecer_fecha(self.fecha_fin, fin)
            self.hora_inicio.delete(0, tk.END); self.hora_inicio.insert(0, ini.strftime("%H:%M"))
            self.hora_fin.delete(0, tk.END); self.hora_fin.insert(0, fin.strftime("%H:%M"))
        except ValueError:
            pass

    def cargar_datosextra_eventos(self, id):
        try:
            rows = self.ejecutar_consulta("""
                SELECT id_tarea, descripcion, date_trunc('second', NOW() - fecha_limite), prioridad 
                FROM tareas 
                WHERE id_evento = %s AND NOW()::timestamp > fecha_limite
                order by fecha_limite asc
            """, (id,),fetch=True)
            for item in self.tree_eventos_tareas.get_children(): self.tree_eventos_tareas.delete(item)
            for row in rows:
                self.tree_eventos_tareas.insert("", "end", values=(row[0], row[1], row[2], row[3]))
                
        except Exception as e:
            print(f"Error cargando Ubicaciones: {e}")

    def limpiar_form_evento(self):
        self.tree_eventos.selection_remove(self.tree_eventos.selection())
        self.entry_ev_titulo.delete(0, tk.END)
        self.combo_ev_usuario.set("Seleccione un usuario")
        self.combo_ev_categoria.set("Seleccione una categoría")
        self.combo_ev_ubicacion.set("Seleccione una ubicacion")
        hoy = datetime.now()
        self.establecer_fecha(self.fecha_inicio, hoy); self.establecer_fecha(self.fecha_fin, hoy)
        self.hora_inicio.delete(0, tk.END); self.hora_inicio.insert(0, "09:00")
        self.hora_fin.delete(0, tk.END); self.hora_fin.insert(0, "10:00")

    def datos_evento_formulario(self):
        titulo = self.entry_ev_titulo.get().strip()
        usuario = self.usuarios_combo.get(self.combo_ev_usuario.get())
        categoria = self.categorias_combo.get(self.combo_ev_categoria.get())
        ubicacion = self.ubicaciones_combo.get(self.combo_ev_ubicacion.get())
        
        try:
            inicio = datetime.strptime(f"{self.obtener_fecha(self.fecha_inicio)} {self.hora_inicio.get().strip()}", "%Y-%m-%d %H:%M")
            fin = datetime.strptime(f"{self.obtener_fecha(self.fecha_fin)} {self.hora_fin.get().strip()}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("La hora debe tener formato HH:MM, por ejemplo 09:30.")
        if not titulo or usuario is None or categoria is None:
            raise ValueError("Completa título, propietario y categoría.")
        if fin <= inicio:
            raise ValueError("La fecha y hora de finalización deben ser posteriores al inicio.")
        return usuario, categoria, titulo, ubicacion, inicio, fin

    def agregar_evento(self):
        try:
            datos = self.datos_evento_formulario()
            self.ejecutar_consulta("""
                INSERT INTO eventos (id_usuario_propietario, id_categoria, titulo, id_ubicacion, fecha_inicio, fecha_fin) 
                VALUES (%s, %s, %s, %s, %s, %s);        
                """, datos)
            self.limpiar_form_evento(); self.cargar_datos_eventos()
            messagebox.showinfo("Éxito", "Evento creado correctamente.")
        except Exception as e:
            messagebox.showerror("No se pudo crear el evento", str(e))

    def actualizar_evento(self):
        eid = self.evento_seleccionado_id()
        if eid is None: return messagebox.showwarning("Selección requerida", "Selecciona un evento.")
        try:
            usuario, categoria, titulo, ubicacion, inicio, fin = self.datos_evento_formulario()
            print(ubicacion)
            self.ejecutar_consulta("""
                UPDATE eventos SET id_usuario_propietario=%s, id_categoria=%s,
                titulo=%s, id_ubicacion=%s, fecha_inicio=%s, fecha_fin=%s WHERE id_evento=%s
            """, (usuario, categoria, titulo, ubicacion, inicio, fin, eid))
            self.cargar_datos_eventos(); messagebox.showinfo("Éxito", "Evento actualizado.")
        except Exception as e:
            messagebox.showerror("No se pudo actualizar", str(e))

    def eliminar_evento(self):
        eid = self.evento_seleccionado_id()
        if eid is None: return messagebox.showwarning("Selección requerida", "Selecciona un evento.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar el evento seleccionado?"): return
        try:
            self.ejecutar_consulta("DELETE FROM eventos WHERE id_evento=%s", (eid,))
            self.limpiar_form_evento(); self.cargar_datos_eventos()
            messagebox.showinfo("Eliminado", "Evento eliminado.")
        except Exception as e:
            messagebox.showerror("No se pudo eliminar", str(e))

    def cargar_datos_eventos(self):
        try:
            rows = self.ejecutar_consulta("""
                SELECT e.id_evento, u.id_usuario, u.nombre, u.apellido,
                       c.id_categoria, c.nombre, e.titulo, u2.id_ubicacion, u2.nombre, e.fecha_inicio, e.fecha_fin
                FROM eventos e
                JOIN usuarios u ON u.id_usuario = e.id_usuario_propietario
                JOIN categorias c ON c.id_categoria = e.id_categoria
                JOIN ubicaciones u2 on u2.id_ubicacion = e.id_ubicacion 
                ORDER BY e.fecha_inicio DESC
            """, fetch=True)
            for item in self.tree_eventos.get_children(): self.tree_eventos.delete(item)
            self.eventos_combo = {}
            for row in rows:
                usuario = f"{row[2]} {row[3]} — #{row[1]}"
                categoria = f"{row[5]} — #{row[4]}"
                ubicacion = f"{row[8]} — #{row[7]}"
                inicio = row[9].strftime("%Y-%m-%d %H:%M") if hasattr(row[9], "strftime") else row[9]
                fin = row[10].strftime("%Y-%m-%d %H:%M") if hasattr(row[10], "strftime") else row[10]
                self.tree_eventos.insert("", "end", values=(row[0], usuario, categoria, row[6], ubicacion, inicio, fin))
                etiqueta = f"{row[6]} — #{row[0]}"
                self.eventos_combo[etiqueta] = row[0]

            valores_u = ["Seleccione un usuario"] + list(self.usuarios_combo.keys())
            valores_c = ["Seleccione una categoría"] + list(self.categorias_combo.keys())
            valores_ub = ["Seleccione una ubicacion"] + list(self.ubicaciones_combo.keys())

            self.combo_ev_usuario.configure(values=valores_u)
            self.combo_ev_categoria.configure(values=valores_c)
            self.combo_ev_ubicacion.configure(values=valores_ub)
        except Exception as e:
            print(f"Error cargando eventos: {e}")

    # -------------------- REFRESCO GENERAL --------------------

    def actualizar_todas_las_tablas(self):
        self.cargar_datos_usuarios()
        self.cargar_datos_categorias()
        self.cargar_datos_ubicaciones()
        self.cargar_datos_eventos()
        self.cargar_datos_reportes()
        self.cargar_datos_tareas()
        self.cargar_reporte_tareas()
        self.cargar_datos_disponibilidades()


if __name__ == "__main__":
    app = AppAgenda()
    app.mainloop()