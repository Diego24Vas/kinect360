/**
 * Lógica Frontend para el control reactivo del visor Kinect 360, motor y zoom de imagen
 */

document.addEventListener("DOMContentLoaded", () => {
    // Selectores de cámaras y sobreposiciones
    const radioCamaras = document.querySelectorAll('input[name="camara"]');
    const radioSobreposicion = document.querySelectorAll('input[name="sobreposicion"]');
    const checkFondoNegro = document.getElementById("checkFondoNegro");

    // Selectores de inclinación del motor
    const sliderTilt = document.getElementById("sliderTilt");
    const lblAnguloActual = document.getElementById("lblAnguloActual");
    const btnTiltBajar = document.getElementById("btnTiltBajar");
    const btnTiltCentrar = document.getElementById("btnTiltCentrar");
    const btnTiltSubir = document.getElementById("btnTiltSubir");

    // Selectores de Zoom
    const streamKinect = document.getElementById("streamKinect");
    const contenedorVideo = streamKinect ? streamKinect.parentElement : null;
    const sliderZoom = document.getElementById("sliderZoom");
    const lblZoomActual = document.getElementById("lblZoomActual");
    const btnZoomMenos = document.getElementById("btnZoomMenos");
    const btnZoomReset = document.getElementById("btnZoomReset");
    const btnZoomMas = document.getElementById("btnZoomMas");

    // Variables de estado del Zoom y Desplazamiento (Pan)
    let zoomNivel = 1.0;
    let panX = 0;
    let panY = 0;
    let arrastrando = false;
    let inicioX = 0;
    let inicioY = 0;

    /**
     * Aplica la transformación CSS de zoom y pan sobre la imagen de video
     */
    function renderizarTransformacion() {
        if (!streamKinect) return;

        // Limitar desplazamiento dentro del área visible según el nivel de zoom
        const maxPanX = (contenedorVideo ? contenedorVideo.clientWidth : 900) * (zoomNivel - 1) / (2 * zoomNivel);
        const maxPanY = (contenedorVideo ? contenedorVideo.clientHeight : 675) * (zoomNivel - 1) / (2 * zoomNivel);

        panX = Math.max(-maxPanX, Math.min(maxPanX, panX));
        panY = Math.max(-maxPanY, Math.min(maxPanY, panY));

        streamKinect.style.transform = `scale(${zoomNivel}) translate(${panX}px, ${panY}px)`;
    }

    /**
     * Ajusta el nivel de zoom y sincroniza los controles visuales
     */
    function ajustarZoom(nuevoNivel, reiniciarPan = false) {
        // Limitar zoom entre 1.0x y 3.5x
        zoomNivel = Math.max(1.0, Math.min(3.5, Math.round(Number(nuevoNivel) * 10) / 10));

        if (reiniciarPan || zoomNivel <= 1.0) {
            panX = 0;
            panY = 0;
        }

        if (contenedorVideo) {
            if (zoomNivel > 1.0) {
                contenedorVideo.classList.add("modo-zoom");
            } else {
                contenedorVideo.classList.remove("modo-zoom");
            }
        }

        renderizarTransformacion();

        // Actualizar etiquetas y slider de zoom
        const textoZoom = `${zoomNivel.toFixed(1)}x`;
        if (sliderZoom) sliderZoom.value = zoomNivel;
        if (lblZoomActual) lblZoomActual.textContent = textoZoom;
    }

    /**
     * Envía la configuración de visualización al servidor
     */
    async function enviarConfiguracion(parametros) {
        try {
            await fetch("/api/settings", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(parametros)
            });
        } catch (error) {
            console.error("Error al actualizar la configuración:", error);
        }
    }

    /**
     * Envía la orden de movimiento de inclinación al motor de la Kinect
     */
    async function moverMotor(angulo) {
        const anguloClamped = Math.max(-30, Math.min(30, Math.round(Number(angulo))));
        
        if (sliderTilt) sliderTilt.value = anguloClamped;
        if (lblAnguloActual) lblAnguloActual.textContent = `${anguloClamped}°`;

        try {
            const respuesta = await fetch("/api/tilt", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ angle: anguloClamped })
            });

            if (respuesta.ok) {
                const datos = await respuesta.json();
                if (lblAnguloActual) lblAnguloActual.textContent = `${datos.angulo}°`;
                if (sliderTilt) sliderTilt.value = datos.angulo;
            }
        } catch (error) {
            console.error("Error al mover el motor:", error);
        }
    }

    // Escuchar cambio en el apartado de Cámara
    radioCamaras.forEach((radio) => {
        radio.addEventListener("change", (e) => {
            if (e.target.checked) {
                enviarConfiguracion({ camara: e.target.value });
            }
        });
    });

    /**
     * Bloquea o desbloquea la opción de Fondo Negro según la sobreposición activa
     */
    function actualizarEstadoBloqueoFondo(sobreposicion) {
        if (!checkFondoNegro) return;
        const esNinguno = (sobreposicion === "ninguno");
        checkFondoNegro.disabled = esNinguno;
        
        const contenedor = document.getElementById("contenedorFondoNegro") || checkFondoNegro.closest(".opcion-control");
        if (contenedor) {
            if (esNinguno) {
                contenedor.classList.add("bloqueado");
                if (checkFondoNegro.checked) {
                    checkFondoNegro.checked = false;
                    enviarConfiguracion({ fondo_negro: false });
                }
            } else {
                contenedor.classList.remove("bloqueado");
            }
        }
    }

    // Escuchar cambio en el apartado de Sobreposición
    radioSobreposicion.forEach((radio) => {
        radio.addEventListener("change", (e) => {
            if (e.target.checked) {
                actualizarEstadoBloqueoFondo(e.target.value);
                enviarConfiguracion({ sobreposicion: e.target.value });
            }
        });
    });

    // Escuchar cambio en la casilla de Fondo Negro
    if (checkFondoNegro) {
        checkFondoNegro.addEventListener("change", (e) => {
            enviarConfiguracion({ fondo_negro: e.target.checked });
        });
    }

    // Controles de motor: Botón Bajar (-5°)
    if (btnTiltBajar) {
        btnTiltBajar.addEventListener("click", () => {
            const actual = Number(sliderTilt?.value || 0);
            moverMotor(actual - 5);
        });
    }

    // Controles de motor: Botón Centrar (0°)
    if (btnTiltCentrar) {
        btnTiltCentrar.addEventListener("click", () => {
            moverMotor(0);
        });
    }

    // Controles de motor: Botón Subir (+5°)
    if (btnTiltSubir) {
        btnTiltSubir.addEventListener("click", () => {
            const actual = Number(sliderTilt?.value || 0);
            moverMotor(actual + 5);
        });
    }

    // Controles de motor: Slider interactivo
    if (sliderTilt) {
        sliderTilt.addEventListener("input", (e) => {
            if (lblAnguloActual) lblAnguloActual.textContent = `${e.target.value}°`;
        });
        sliderTilt.addEventListener("change", (e) => {
            moverMotor(e.target.value);
        });
    }

    // --------------------------------------------------------------------------
    // Controles de Zoom
    // --------------------------------------------------------------------------
    if (sliderZoom) {
        sliderZoom.addEventListener("input", (e) => {
            ajustarZoom(e.target.value);
        });
    }

    if (btnZoomMenos) {
        btnZoomMenos.addEventListener("click", () => {
            ajustarZoom(zoomNivel - 0.25);
        });
    }

    if (btnZoomReset) {
        btnZoomReset.addEventListener("click", () => {
            ajustarZoom(1.0, true);
        });
    }

    if (btnZoomMas) {
        btnZoomMas.addEventListener("click", () => {
            ajustarZoom(zoomNivel + 0.25);
        });
    }

    // Zoom con la rueda del ratón directamente sobre el visor
    if (contenedorVideo) {
        contenedorVideo.addEventListener("wheel", (e) => {
            e.preventDefault();
            const delta = e.deltaY < 0 ? 0.2 : -0.2;
            ajustarZoom(zoomNivel + delta);
        }, { passive: false });

        // Doble clic para alternar entre zoom 2x y 1x
        contenedorVideo.addEventListener("dblclick", () => {
            if (zoomNivel > 1.0) {
                ajustarZoom(1.0, true);
            } else {
                ajustarZoom(2.0, true);
            }
        });

        // Arrastrar (pan) cuando hay zoom activo
        contenedorVideo.addEventListener("mousedown", (e) => {
            if (zoomNivel <= 1.0) return;
            arrastrando = true;
            inicioX = e.clientX - panX * zoomNivel;
            inicioY = e.clientY - panY * zoomNivel;
            contenedorVideo.classList.add("modo-arrastre");
        });

        window.addEventListener("mousemove", (e) => {
            if (!arrastrando) return;
            panX = (e.clientX - inicioX) / zoomNivel;
            panY = (e.clientY - inicioY) / zoomNivel;
            renderizarTransformacion();
        });

        window.addEventListener("mouseup", () => {
            if (arrastrando) {
                arrastrando = false;
                contenedorVideo.classList.remove("modo-arrastre");
            }
        });
    }

    // Inicializar estado de bloqueo de Fondo Negro al cargar
    const sobreposicionInicial = document.querySelector('input[name="sobreposicion"]:checked')?.value || "ninguno";
    actualizarEstadoBloqueoFondo(sobreposicionInicial);
});

