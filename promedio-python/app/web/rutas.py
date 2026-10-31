"""Rutas de la aplicación web local."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response

from app.core.errores import ErrorAcademico
from app.core.texto import clave_nombre
from app.core.tiempo import hoy_iso
from app.services.exportacion import ExportacionService
from app.services.fabrica import Servicios
from app.web.dependencias import servicios_lectura, servicios_escritura
from app.web.plantillas import plantillas

router = APIRouter()


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def _redirigir(
    destino: str, mensaje: str | None = None, tipo: str = "ok"
) -> RedirectResponse:
    if mensaje:
        separador = "&" if "?" in destino else "?"
        destino = f"{destino}{separador}mensaje={quote(mensaje)}&tipo={tipo}"
    return RedirectResponse(destino, status_code=303)


def _render(request: Request, plantilla: str, activo: str, **extra):
    contexto = {
        "request": request,
        "activo": activo,
        "hoy": datetime.now().strftime("%d/%m/%Y"),
        "mensaje": request.query_params.get("mensaje"),
        "tipo": request.query_params.get("tipo", "ok"),
    }
    contexto.update(extra)
    return plantillas.TemplateResponse(
        request=request, name=plantilla, context=contexto
    )


def _porcentajes(aprobados: int, reprobados: int, sin_notas: int) -> dict[str, float]:
    total = aprobados + reprobados + sin_notas
    if total <= 0:
        return {"aprobados": 0.0, "reprobados": 0.0, "sin_notas": 100.0}
    return {
        "aprobados": round(aprobados * 100 / total, 1),
        "reprobados": round(reprobados * 100 / total, 1),
        "sin_notas": round(sin_notas * 100 / total, 1),
    }


def _maximo(puntos) -> float:
    return max((punto.valor for punto in puntos), default=0.0) or 1.0


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------
@router.get("/")
def dashboard(
    request: Request,
    servicios: Servicios = Depends(servicios_lectura),
):
    resumen = servicios.analisis.resumen()
    return _render(
        request,
        "dashboard.html",
        "dashboard",
        resumen=resumen,
        porcentajes=_porcentajes(
            resumen.aprobados, resumen.reprobados, resumen.sin_notas
        ),
        max_materia=_maximo(resumen.por_materia),
        ranking=sorted(
            resumen.estudiantes,
            key=lambda fila: (
                fila.promedio is None,
                -(fila.promedio or 0.0),
                fila.estudiante.nombre,
            ),
        )[:8],
    )


# ----------------------------------------------------------------------
# Estudiantes
# ----------------------------------------------------------------------
@router.get("/estudiantes")
def estudiantes(
    request: Request,
    busqueda: str = "",
    servicios: Servicios = Depends(servicios_lectura),
):
    resumen = servicios.analisis.resumen()
    texto = clave_nombre(busqueda.strip()) if busqueda.strip() else ""
    filas = [
        fila
        for fila in resumen.estudiantes
        if not texto
        or texto in clave_nombre(fila.estudiante.nombre)
        or texto in fila.estudiante.codigo.casefold()
    ]
    filas.sort(key=lambda fila: fila.estudiante.nombre)
    return _render(
        request,
        "estudiantes.html",
        "estudiantes",
        filas=filas,
        busqueda=busqueda,
    )


@router.get("/estudiantes/nuevo")
def nuevo_estudiante(request: Request):
    return _render(
        request,
        "formulario_estudiante.html",
        "estudiantes",
        estudiante=None,
    )


@router.get("/estudiantes/{estudiante_id}/editar")
def editar_estudiante(
    request: Request,
    estudiante_id: str,
    servicios: Servicios = Depends(servicios_lectura),
):
    try:
        estudiante = servicios.estudiantes.obtener(estudiante_id)
    except ErrorAcademico as error:
        return _redirigir("/estudiantes", str(error), "error")
    return _render(
        request,
        "formulario_estudiante.html",
        "estudiantes",
        estudiante=estudiante,
    )


@router.post("/estudiantes/guardar")
def guardar_estudiante(
    nombre: str = Form(...),
    correo: str = Form(""),
    identificador: str = Form(""),
    servicios: Servicios = Depends(servicios_escritura),
):
    try:
        if identificador:
            servicios.estudiantes.actualizar(
                identificador, nombre=nombre, correo=correo
            )
            mensaje = "Estudiante actualizado correctamente."
        else:
            servicios.estudiantes.crear(nombre, correo or None)
            mensaje = "Estudiante registrado correctamente."
    except (ErrorAcademico, ValueError) as error:
        return _redirigir("/estudiantes", str(error), "error")
    return _redirigir("/estudiantes", mensaje)


@router.post("/estudiantes/{estudiante_id}/eliminar")
def eliminar_estudiante(
    estudiante_id: str,
    servicios: Servicios = Depends(servicios_escritura),
):
    try:
        servicios.estudiantes.eliminar(estudiante_id)
    except (ErrorAcademico, ValueError) as error:
        return _redirigir("/estudiantes", str(error), "error")
    return _redirigir(
        "/estudiantes",
        "Estudiante eliminado del listado activo; sus notas se conservan.",
    )


# ----------------------------------------------------------------------
# Materias
# ----------------------------------------------------------------------
@router.get("/materias")
def materias(
    request: Request,
    busqueda: str = "",
    servicios: Servicios = Depends(servicios_lectura),
):
    lista = servicios.materias.listar()
    detalles = servicios.calificaciones.listar_todas()
    conteo = Counter(detalle.materia_id for detalle in detalles)

    texto = clave_nombre(busqueda.strip()) if busqueda.strip() else ""
    lista = [
        materia
        for materia in lista
        if not texto
        or texto in clave_nombre(materia.nombre)
        or texto in materia.codigo.casefold()
    ]
    lista.sort(key=lambda materia: materia.codigo)
    return _render(
        request,
        "materias.html",
        "materias",
        materias=lista,
        conteo=conteo,
        busqueda=busqueda,
    )


@router.get("/materias/nuevo")
def nueva_materia(request: Request):
    return _render(
        request,
        "formulario_materia.html",
        "materias",
        materia=None,
    )


@router.get("/materias/{materia_id}/editar")
def editar_materia(
    request: Request,
    materia_id: str,
    servicios: Servicios = Depends(servicios_lectura),
):
    try:
        materia = servicios.materias.obtener(materia_id)
    except ErrorAcademico as error:
        return _redirigir("/materias", str(error), "error")
    return _render(
        request,
        "formulario_materia.html",
        "materias",
        materia=materia,
    )


@router.post("/materias/guardar")
def guardar_materia(
    codigo: str = Form(...),
    nombre: str = Form(...),
    creditos: str = Form("0"),
    identificador: str = Form(""),
    servicios: Servicios = Depends(servicios_escritura),
):
    try:
        valor_creditos = float(creditos.strip().replace(",", ".") or 0)
        if identificador:
            servicios.materias.actualizar(
                identificador,
                codigo=codigo,
                nombre=nombre,
                creditos=valor_creditos,
            )
            mensaje = "Materia actualizada correctamente."
        else:
            servicios.materias.crear(codigo, nombre, valor_creditos)
            mensaje = "Materia registrada correctamente."
    except (ErrorAcademico, ValueError) as error:
        return _redirigir("/materias", str(error), "error")
    return _redirigir("/materias", mensaje)


@router.post("/materias/{materia_id}/eliminar")
def eliminar_materia(
    materia_id: str,
    servicios: Servicios = Depends(servicios_escritura),
):
    try:
        servicios.materias.eliminar(materia_id)
    except (ErrorAcademico, ValueError) as error:
        return _redirigir("/materias", str(error), "error")
    return _redirigir(
        "/materias",
        "Materia eliminada del catálogo activo; sus notas se conservan.",
    )


# ----------------------------------------------------------------------
# Calificaciones
# ----------------------------------------------------------------------
@router.get("/calificaciones")
def calificaciones(
    request: Request,
    estudiante_id: str = "",
    periodo_id: str = "",
    servicios: Servicios = Depends(servicios_lectura),
):
    estudiantes = servicios.estudiantes.listar()
    materias = servicios.materias.listar()
    periodos = servicios.periodos.listar()

    ids_estudiantes = {estudiante.id for estudiante in estudiantes}
    ids_periodos = {periodo.id for periodo in periodos}
    if estudiante_id not in ids_estudiantes:
        estudiante_id = ""
    if periodo_id not in ids_periodos:
        periodo_id = ""

    detalles = servicios.calificaciones.listar_todas(
        estudiante_id=estudiante_id or None,
        periodo_id=periodo_id or None,
    )
    escalas = {periodo.id: periodo.escala for periodo in periodos}
    filas = [
        {
            "detalle": detalle,
            "estado": escalas[detalle.periodo_id].estado(detalle.nota),
        }
        for detalle in detalles
        if detalle.periodo_id in escalas
    ]
    notas = [fila["detalle"].nota for fila in filas]

    return _render(
        request,
        "calificaciones.html",
        "calificaciones",
        estudiantes=estudiantes,
        materias=materias,
        periodos=periodos,
        filas=filas,
        filtro_estudiante=estudiante_id,
        filtro_periodo=periodo_id,
        promedio_filtro=(sum(notas) / len(notas)) if notas else None,
        fecha_hoy=hoy_iso(),
    )


@router.post("/calificaciones/nueva")
def registrar_calificacion(
    estudiante_id: str = Form(...),
    materia_id: str = Form(...),
    periodo_id: str = Form(...),
    nota: str = Form(...),
    fecha: str = Form(""),
    descripcion: str = Form(""),
    servicios: Servicios = Depends(servicios_escritura),
):
    try:
        valor = float(nota.strip().replace(",", "."))
        fecha_registro = fecha.strip() or None
        if fecha_registro is not None:
            datetime.strptime(fecha_registro, "%Y-%m-%d")
        servicios.calificaciones.registrar(
            estudiante_id,
            materia_id,
            periodo_id,
            valor,
            descripcion=descripcion.strip() or None,
            fecha=fecha_registro,
        )
    except (ErrorAcademico, ValueError) as error:
        return _redirigir("/calificaciones", str(error), "error")
    return _redirigir("/calificaciones", "Calificación registrada correctamente.")


@router.post("/calificaciones/{calificacion_id}/anular")
def anular_calificacion(
    calificacion_id: str,
    servicios: Servicios = Depends(servicios_escritura),
):
    try:
        servicios.calificaciones.anular(calificacion_id)
    except (ErrorAcademico, ValueError) as error:
        return _redirigir("/calificaciones", str(error), "error")
    return _redirigir(
        "/calificaciones",
        "Calificación anulada; la nota se conserva en SQLite.",
    )


# ----------------------------------------------------------------------
# Historial
# ----------------------------------------------------------------------
@router.get("/historial")
def historial(
    request: Request,
    estudiante_id: str = "",
    busqueda: str = "",
    servicios: Servicios = Depends(servicios_lectura),
):
    resumen = servicios.analisis.resumen()
    todas = resumen.estudiantes
    texto = clave_nombre(busqueda.strip()) if busqueda.strip() else ""
    filas = [
        fila
        for fila in todas
        if not texto
        or texto in clave_nombre(fila.estudiante.nombre)
        or texto in fila.estudiante.codigo.casefold()
    ]
    filas.sort(key=lambda fila: fila.estudiante.nombre)

    ids_validos = {fila.estudiante.id for fila in todas}
    if estudiante_id not in ids_validos:
        estudiante_id = filas[0].estudiante.id if filas else ""

    detalle = (
        servicios.analisis.detalle_estudiante(estudiante_id)
        if estudiante_id
        else None
    )
    return _render(
        request,
        "historial.html",
        "historial",
        filas=filas,
        detalle=detalle,
        estudiante_id=estudiante_id,
        busqueda=busqueda,
    )


# ----------------------------------------------------------------------
# Estadísticas
# ----------------------------------------------------------------------
@router.get("/estadisticas")
def estadisticas(
    request: Request,
    periodo_id: str = "",
    servicios: Servicios = Depends(servicios_lectura),
):
    periodos = servicios.periodos.listar()
    ids_periodos = {periodo.id for periodo in periodos}
    if periodo_id not in ids_periodos:
        periodo_id = ""

    resumen = servicios.analisis.resumen(periodo_id=periodo_id or None)
    return _render(
        request,
        "estadisticas.html",
        "estadisticas",
        resumen=resumen,
        periodos=periodos,
        filtro_periodo=periodo_id,
        max_materia=_maximo(resumen.por_materia),
        max_periodo=_maximo(resumen.por_periodo),
        ranking=sorted(
            resumen.estudiantes,
            key=lambda fila: (
                fila.promedio is None,
                -(fila.promedio or 0.0),
                fila.estudiante.nombre,
            ),
        ),
    )


# ----------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------
@router.get("/configuracion")
def configuracion(
    request: Request,
    servicios: Servicios = Depends(servicios_lectura),
):
    escala = servicios.configuracion.obtener_escala()
    periodos = servicios.periodos.listar(incluir_inactivos=True)
    return _render(
        request,
        "configuracion.html",
        "configuracion",
        escala=escala,
        periodos=periodos,
    )


@router.post("/configuracion/escala")
def guardar_escala(
    minima: str = Form(...),
    maxima: str = Form(...),
    aprobacion: str = Form(...),
    decimales: str = Form("2"),
    servicios: Servicios = Depends(servicios_escritura),
):
    try:
        servicios.configuracion.actualizar_escala(
            float(minima.strip().replace(",", ".")),
            float(maxima.strip().replace(",", ".")),
            float(aprobacion.strip().replace(",", ".")),
            int(decimales),
        )
    except (ErrorAcademico, ValueError) as error:
        return _redirigir("/configuracion", str(error), "error")
    return _redirigir(
        "/configuracion",
        "Escala global actualizada. Los periodos existentes conservan la suya.",
    )


@router.get("/periodos/nuevo")
def nuevo_periodo(
    request: Request,
    servicios: Servicios = Depends(servicios_lectura),
):
    escala = servicios.configuracion.obtener_escala()
    return _render(
        request,
        "formulario_periodo.html",
        "configuracion",
        periodo=None,
        escala=escala,
    )


@router.get("/periodos/{periodo_id}/editar")
def editar_periodo(
    request: Request,
    periodo_id: str,
    servicios: Servicios = Depends(servicios_lectura),
):
    try:
        periodo = servicios.periodos.obtener(periodo_id)
    except ErrorAcademico as error:
        return _redirigir("/configuracion", str(error), "error")
    return _render(
        request,
        "formulario_periodo.html",
        "configuracion",
        periodo=periodo,
        escala=periodo.escala,
    )


@router.post("/periodos/guardar")
def guardar_periodo(
    nombre: str = Form(...),
    fecha_inicio: str = Form(""),
    fecha_fin: str = Form(""),
    minima: str = Form(...),
    maxima: str = Form(...),
    aprobacion: str = Form(...),
    activo: str = Form(""),
    identificador: str = Form(""),
    servicios: Servicios = Depends(servicios_escritura),
):
    try:
        from app.core.escala import Escala

        escala = Escala(
            minima=float(minima.strip().replace(",", ".")),
            maxima=float(maxima.strip().replace(",", ".")),
            aprobacion=float(aprobacion.strip().replace(",", ".")),
        )
        datos = {
            "nombre": nombre,
            "fecha_inicio": fecha_inicio.strip() or None,
            "fecha_fin": fecha_fin.strip() or None,
            "escala": escala,
            "activo": bool(activo),
        }
        if identificador:
            servicios.periodos.actualizar(identificador, **datos)
            mensaje = "Periodo actualizado correctamente."
        else:
            servicios.periodos.crear(**datos)
            mensaje = "Periodo creado con su escala académica."
    except (ErrorAcademico, ValueError) as error:
        return _redirigir("/configuracion", str(error), "error")
    return _redirigir("/configuracion", mensaje)


# ----------------------------------------------------------------------
# Exportaciones
# ----------------------------------------------------------------------
_TIPOS_EXPORTACION = {"estudiantes", "calificaciones"}
_FORMATOS = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


@router.get("/exportar/{tipo}.{formato}")
def exportar(
    tipo: str,
    formato: str,
    servicios: Servicios = Depends(servicios_lectura),
):
    if tipo not in _TIPOS_EXPORTACION or formato not in _FORMATOS:
        raise HTTPException(status_code=404, detail="Exportación no disponible.")

    exportacion = ExportacionService(servicios)
    # El servicio nombra el método ``_excel``; la URL usa la extensión ``xlsx``.
    metodo = "excel" if formato == "xlsx" else formato
    contenido = getattr(exportacion, f"{tipo}_{metodo}")()
    nombre = f"{tipo}-{datetime.now().strftime('%Y%m%d')}.{formato}"
    return Response(
        content=contenido,
        media_type=_FORMATOS[formato],
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


# ----------------------------------------------------------------------
# Salud del servicio
# ----------------------------------------------------------------------
@router.get("/salud")
def salud(
    request: Request,
    servicios: Servicios = Depends(servicios_lectura),
):
    return {
        "estado": "ok",
        "base": str(request.app.state.ruta_db),
        "estudiantes": servicios.estudiantes.contar(),
        "materias": len(servicios.materias.listar()),
        "periodos": len(servicios.periodos.listar(incluir_inactivos=True)),
    }
