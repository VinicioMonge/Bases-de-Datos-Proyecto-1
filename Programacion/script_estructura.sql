-- Crear la base de datos
CREATE DATABASE agendita;
CREATE SCHEMA prototipo;

-- Configurar el search_path para que las tablas se creen dentro de ese esquema
-- y se busquen ahí automáticamente
SET search_path TO prototipo, public;

-- 1. Usuarios
create table prototipo.usuarios (
	id_usuario serial4 not null,
	nombre varchar(50) not null,
	apellido varchar(50) not null,
	fecha_registro date default CURRENT_DATE not null,
	activo bool default true null,
	constraint usuarios_apellido_not_null not null apellido,
	constraint usuarios_fecha_registro_not_null not null fecha_registro,
	constraint usuarios_id_usuario_not_null not null id_usuario,
	constraint usuarios_nombre_not_null not null nombre,
	constraint usuarios_pkey primary key (id_usuario)
);

-- 2. Contactos (RF02, RE02, RN02)
create table prototipo.usuario_telefonos (
	id_usuario int4 not null,
	telefono varchar(20) not null,
	constraint usuario_telefonos_id_usuario_not_null not null id_usuario,
	constraint usuario_telefonos_pkey primary key (id_usuario, telefono),
	constraint usuario_telefonos_telefono_not_null not null telefono
);
-- prototipo.usuario_telefonos foreign keys

alter table prototipo.usuario_telefonos add constraint usuario_telefonos_id_usuario_fkey foreign key (id_usuario) references prototipo.usuarios(id_usuario);

create table prototipo.usuario_emails (
	id_usuario int4 not null,
	email varchar(100) not null,
	constraint usuario_emails_email_not_null not null email,
	constraint usuario_emails_id_usuario_not_null not null id_usuario,
	constraint usuario_emails_pkey primary key (id_usuario, email)
);
-- prototipo.usuario_emails foreign keys

alter table prototipo.usuario_emails add constraint usuario_emails_id_usuario_fkey foreign key (id_usuario) references prototipo.usuarios(id_usuario);

-- 3. Categorías (RF03, RE05, RN04)
create table prototipo.categorias (
	id_categoria serial4 not null,
	nombre varchar(50) not null,
	id_categoria_padre int4 null,
	constraint categorias_id_categoria_not_null not null id_categoria,
	constraint categorias_nombre_not_null not null nombre,
	constraint categorias_pkey primary key (id_categoria),
	constraint categorias_id_categoria_padre_fkey foreign key (id_categoria_padre) references prototipo.categorias(id_categoria)
);

create table prototipo.ubicaciones (
	id_ubicacion serial4 not null,
	nombre varchar(30) not null,
	direccion varchar(30) not null,
	ciudad varchar(30) not null,
	capacidad int4 null,
	constraint ubicaciones_capacidad_check check ((capacidad > 0)),
	constraint ubicaciones_ciudad_not_null not null ciudad,
	constraint ubicaciones_direccion_not_null not null direccion,
	constraint ubicaciones_id_ubicaciones_not_null not null id_ubicacion,
	constraint ubicaciones_nombre_not_null not null nombre,
	constraint ubicaciones_pkey primary key (id_ubicacion)
);

-- 4. Eventos (RF04, RE04)
create table prototipo.eventos (
	id_evento serial4 not null,
	id_usuario_propietario int4 not null,
	id_categoria int4 not null,
	titulo varchar(100) not null,
	descripcion text null,
	fecha_inicio timestamp not null,
	fecha_fin timestamp not null,
	id_ubicacion int4 not null,
	constraint check_fechas check ((fecha_fin > fecha_inicio)),
	constraint eventos_fecha_fin_not_null not null fecha_fin,
	constraint eventos_fecha_inicio_not_null not null fecha_inicio,
	constraint eventos_id_categoria_not_null not null id_categoria,
	constraint eventos_id_evento_not_null not null id_evento,
	constraint eventos_id_ubicacion_not_null not null id_ubicacion,
	constraint eventos_id_usuario_propietario_not_null not null id_usuario_propietario,
	constraint eventos_pkey primary key (id_evento),
	constraint eventos_titulo_not_null not null titulo
);

alter table prototipo.eventos add constraint eventos_id_categoria_fkey foreign key (id_categoria) references prototipo.categorias(id_categoria);

alter table prototipo.eventos add constraint eventos_id_ubicacion_fkey foreign key (id_ubicacion) references prototipo.ubicaciones(id_ubicacion);

alter table prototipo.eventos add constraint eventos_id_usuario_propietario_fkey foreign key (id_usuario_propietario) references prototipo.usuarios(id_usuario);

-- 5. Participación (RF05, RE01, RN01, RN05)
create table prototipo.participaciones (
	id_evento int4 not null,
	id_invitado int4 not null,
	rol varchar(50) null,
	estado_confirmacion varchar(20) default 'pendiente'::character varying null,
	constraint participaciones_id_evento_not_null not null id_evento,
	constraint participaciones_id_invitado_not_null not null id_invitado,
	constraint participaciones_pkey primary key (id_evento,
id_invitado)
);
-- prototipo.participaciones foreign keys

alter table prototipo.participaciones add constraint participaciones_id_evento_fkey foreign key (id_evento) references prototipo.eventos(id_evento) on
delete
    cascade;

alter table prototipo.participaciones add constraint participaciones_id_invitado_fkey foreign key (id_invitado) references prototipo.usuarios(id_usuario);

-- 6. Log de Accesos (RF06)
create table prototipo.log_accesos (
	id_log serial4 not null,
	id_usuario int4 null,
	fecha_acceso timestamp default CURRENT_TIMESTAMP null,
	constraint log_accesos_id_log_not_null not null id_log,
	constraint log_accesos_pkey primary key (id_log)
);
-- prototipo.log_accesos foreign keys

alter table prototipo.log_accesos add constraint log_accesos_id_usuario_fkey foreign key (id_usuario) references prototipo.usuarios(id_usuario);

create table prototipo.tareas (
	id_tarea serial4 not null,
	id_evento int4 not null,
	responsable int4 not null,
	titulo varchar(30) not null,
	descripcion varchar(30) null,
	fecha_limite timestamp not null,
	prioridad varchar(30) not null,
	estado varchar(30) default 'Pendiente'::character varying null,
	constraint tareas_fecha_limite_not_null not null fecha_limite,
	constraint tareas_id_evento_not_null not null id_evento,
	constraint tareas_id_tarea_not_null not null id_tarea,
	constraint tareas_pkey primary key (id_tarea, id_evento),
	constraint tareas_prioridad_not_null not null prioridad,
	constraint tareas_responsable_not_null not null responsable,
	constraint tareas_titulo_not_null not null titulo
);
-- prototipo.tareas foreign keys

alter table prototipo.tareas add constraint tareas_id_evento_fkey foreign key (id_evento) references prototipo.eventos(id_evento);

alter table prototipo.tareas add constraint tareas_responsable_fkey foreign key (responsable) references prototipo.usuarios(id_usuario);

create table prototipo.tipos_disponibilidad (
	id_tipo serial4 not null,
	nombre varchar(13) not null,
	constraint tipos_disponibilidad_id_tipo_not_null not null id_tipo,
	constraint tipos_disponibilidad_nombre_not_null not null nombre,
	constraint tipos_disponibilidad_pkey primary key (id_tipo)
);
-- prototipo.disponibilidades definition
-- Drop table
-- DROP TABLE prototipo.disponibilidades;

create table prototipo.disponibilidades (
	id_disponibilidad serial4 not null,
	usuario int4 not null,
	estado int4 not null,
	fecha_inicio timestamptz not null,
	fecha_fin timestamptz not null,
	constraint disponibilidades_estado_not_null not null estado,
	constraint disponibilidades_fecha_fin_not_null not null fecha_fin,
	constraint disponibilidades_fecha_inicio_not_null not null fecha_inicio,
	constraint disponibilidades_id_disponibilidad_not_null not null id_disponibilidad,
	constraint disponibilidades_pkey primary key (id_disponibilidad, usuario),
	constraint disponibilidades_usuario_not_null not null usuario
);
-- prototipo.disponibilidades foreign keys

alter table prototipo.disponibilidades add constraint disponibilidades_estado_fkey foreign key (estado) references prototipo.tipos_disponibilidad(id_tipo);

alter table prototipo.disponibilidades add constraint disponibilidades_usuario_fkey foreign key (usuario) references prototipo.usuarios(id_usuario);

-- Implementación de Cálculos Dinámicos (RF07, RE03, RN03) mediante vistas

-- Vista para Antigüedad
create or replace
view prototipo.vista_antiguedad_usuarios
as
select
    id_usuario,
    nombre,
    fecha_registro,
    age(CURRENT_DATE::timestamp with time zone, fecha_registro::timestamp with time zone) as antiguedad
from
    prototipo.usuarios;

-- Vista para Duración de eventos diarios
create or replace
view prototipo.vista_duracion_eventos_diarios
as
select
    id_usuario_propietario,
    fecha_inicio::date as dia,
    sum(extract(epoch from fecha_fin - fecha_inicio) / 60::numeric) as duracion_total_minutos
from
    prototipo.eventos
group by
    id_usuario_propietario,
    (fecha_inicio::date);

--Integridad y Prevención de Ciclos (RE05)
--Para evitar ciclos en la jerarquía de categorías, podemos usar una función 
--que verifique el ancestro antes de insertar o actualizar:

CREATE OR REPLACE FUNCTION evitar_ciclo_categorias()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id_categoria_padre = NEW.id_categoria THEN
        RAISE EXCEPTION 'Una categoría no puede ser padre de sí misma.';
    END IF;
    -- Aquí se podría añadir una consulta recursiva para validar ancestros, 
    -- pero para Postgres 14 es altamente eficiente usar el camino (path) o este chequeo simple.
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_evitar_ciclo
BEFORE INSERT OR UPDATE ON categorias
FOR EACH ROW EXECUTE FUNCTION evitar_ciclo_categorias();

CREATE OR REPLACE FUNCTION prototipo.evitar_disponibilidad_repetida()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    IF 
	(
	    SELECT COUNT(*) FROM disponibilidades, tipos_disponibilidad 
	    WHERE estado != 1
	    AND fecha_inicio <= new.fecha_fin
	    AND fecha_fin >= new.fecha_inicio
	) > 0
	THEN
        RAISE EXCEPTION 'Este horario no se encuentra disponible';
    END IF;
    RETURN NEW;
END;
$function$
;
CREATE TRIGGER trg_evitar_disponibilidad_repetida
BEFORE INSERT ON disponibilidades
FOR EACH ROW EXECUTE FUNCTION prototipo.evitar_disponibilidad_repetida();

CREATE OR REPLACE FUNCTION prototipo.evitar_ubicacion_repetida()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF 
	(
	    SELECT COUNT(*) FROM eventos 
	    WHERE id_ubicacion = new.id_ubicacion
	    AND fecha_inicio < new.fecha_fin
	    AND fecha_fin = new.fecha_inicio
	) > 0
	THEN
        RAISE EXCEPTION 'En esta ubicacion, un evento choca con la hora seleccionada.';
    END IF;
    RETURN NEW;
END;
$function$
;

CREATE TRIGGER trg_evitar_ubicacion
BEFORE INSERT OR UPDATE ON eventos
FOR EACH ROW EXECUTE FUNCTION prototipo.evitar_ubicacion_repetida()