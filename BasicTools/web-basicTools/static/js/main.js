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

    /**
     * Bloquea o desbloquea las opciones de Sobreponer y Fondo según la cámara seleccionada
     */
    function actualizarEstadoCamara(tipoCamara) {
        const esSensor = (tipoCamara === "sensor");

        // Bloquear o desbloquear radios de sobreposición
        radioSobreposicion.forEach((radio) => {
            radio.disabled = esSensor;
            const contenedor = radio.closest(".opcion-control");
            if (contenedor) {
                if (esSensor) {
                    contenedor.classList.add("bloqueado");
                } else {
                    contenedor.classList.remove("bloqueado");
                }
            }
        });

        if (esSensor) {
            // En modo sensor, restablecer sobreposición a 'ninguno'
            const radioNinguno = document.querySelector('input[name="sobreposicion"][value="ninguno"]');
            if (radioNinguno) {
                radioNinguno.checked = true;
            }
            // Bloquear y desmarcar Fondo Negro
            if (checkFondoNegro) {
                checkFondoNegro.checked = false;
                checkFondoNegro.disabled = true;
            }
            const contenedorFondo = document.getElementById("contenedorFondoNegro");
            if (contenedorFondo) {
                contenedorFondo.classList.add("bloqueado");
            }
        } else {
            // Al volver a RGB, sincronizar estado de Fondo Negro con la sobreposición actual
            const sobreActiva = document.querySelector('input[name="sobreposicion"]:checked')?.value || "ninguno";
            actualizarEstadoBloqueoFondo(sobreActiva);
        }
    }

    /**
     * Bloquea o desbloquea la opción de Fondo Negro según la cámara y sobreposición activa
     */
    function actualizarEstadoBloqueoFondo(sobreposicion) {
        if (!checkFondoNegro) return;
        const camaraActual = document.querySelector('input[name="camara"]:checked')?.value || "rgb";
        const esSensor = (camaraActual === "sensor");
        const esNinguno = (sobreposicion === "ninguno");
        const bloqueado = esSensor || esNinguno;

        checkFondoNegro.disabled = bloqueado;
        
        const contenedor = document.getElementById("contenedorFondoNegro") || checkFondoNegro.closest(".opcion-control");
        if (contenedor) {
            if (bloqueado) {
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

    // Escuchar cambio en el apartado de Cámara
    radioCamaras.forEach((radio) => {
        radio.addEventListener("change", (e) => {
            if (e.target.checked) {
                const nuevaCamara = e.target.value;
                actualizarEstadoCamara(nuevaCamara);
                if (nuevaCamara === "sensor") {
                    enviarConfiguracion({
                        camara: "sensor",
                        sobreposicion: "ninguno",
                        fondo_negro: false
                    });
                } else {
                    const sobreActual = document.querySelector('input[name="sobreposicion"]:checked')?.value || "ninguno";
                    enviarConfiguracion({
                        camara: "rgb",
                        sobreposicion: sobreActual,
                        fondo_negro: Boolean(checkFondoNegro?.checked)
                    });
                }
            }
        });
    });

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

    // --------------------------------------------------------------------------
    // Módulo de Captura de Fotografías y Temporizador
    // --------------------------------------------------------------------------
    const btnsTemp = document.querySelectorAll(".btn-temp");
    const btnCapturarFoto = document.getElementById("btnCapturarFoto");
    const btnCancelarFoto = document.getElementById("btnCancelarFoto");
    const textoBtnFoto = document.getElementById("textoBtnFoto");
    const segundosRestantes = document.getElementById("segundosRestantes");
    const notificacionFoto = document.getElementById("notificacionFoto");
    const linkFotoGuardada = document.getElementById("linkFotoGuardada");
    const overlayConteo = document.getElementById("overlayConteo");
    const numeroConteo = document.getElementById("numeroConteo");
    const flashPantalla = document.getElementById("flashPantalla");

    let temporizadorSegundos = 0;
    let temporizadorIntervalo = null;
    let audioCtx = null;

    function reproducirSonido(tipo) {
        try {
            if (!audioCtx) {
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                if (AudioContextClass) {
                    audioCtx = new AudioContextClass();
                }
            }
            if (!audioCtx) return;
            if (audioCtx.state === "suspended") {
                audioCtx.resume();
            }

            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain);
            gain.connect(audioCtx.destination);

            const ahora = audioCtx.currentTime;
            if (tipo === "conteo") {
                // Beep corto de conteo
                osc.type = "sine";
                osc.frequency.setValueAtTime(800, ahora);
                gain.gain.setValueAtTime(0.15, ahora);
                gain.gain.exponentialRampToValueAtTime(0.001, ahora + 0.08);
                osc.start(ahora);
                osc.stop(ahora + 0.08);
            } else if (tipo === "foto") {
                // Sonido de obturador fotográfico
                osc.type = "triangle";
                osc.frequency.setValueAtTime(1200, ahora);
                osc.frequency.exponentialRampToValueAtTime(300, ahora + 0.12);
                gain.gain.setValueAtTime(0.25, ahora);
                gain.gain.exponentialRampToValueAtTime(0.001, ahora + 0.15);
                osc.start(ahora);
                osc.stop(ahora + 0.15);
            }
        } catch (e) {
            // Silencioso en caso de políticas de audio del navegador
        }
    }

    function animarFlash() {
        if (!flashPantalla) return;
        flashPantalla.classList.add("disparo");
        setTimeout(() => {
            flashPantalla.classList.remove("disparo");
        }, 50);
    }

    // Selección de botones del temporizador (0s, 2s, 5s, 10s)
    btnsTemp.forEach((btn) => {
        btn.addEventListener("click", () => {
            btnsTemp.forEach((b) => b.classList.remove("activo"));
            btn.classList.add("activo");
            temporizadorSegundos = parseInt(btn.dataset.segundos, 10) || 0;
        });
    });

    let timerOcultarNotif = null;

    /**
     * Muestra la notificación de foto capturada durante unos segundos y luego la oculta suavemente
     */
    function mostrarNotificacionFoto(nombreArchivo, urlFoto) {
        if (!notificacionFoto) return;

        if (linkFotoGuardada) {
            linkFotoGuardada.textContent = nombreArchivo;
            linkFotoGuardada.href = urlFoto;
        }

        // Si había una cuenta previa para ocultar, reiniciarla
        if (timerOcultarNotif) {
            clearTimeout(timerOcultarNotif);
            timerOcultarNotif = null;
        }

        notificacionFoto.style.display = "flex";
        requestAnimationFrame(() => {
            notificacionFoto.classList.remove("ocultando");
            notificacionFoto.classList.add("visible");
        });

        // Desaparecer después de 4 segundos
        timerOcultarNotif = setTimeout(() => {
            notificacionFoto.classList.remove("visible");
            notificacionFoto.classList.add("ocultando");
            setTimeout(() => {
                notificacionFoto.style.display = "none";
                notificacionFoto.classList.remove("ocultando");
                timerOcultarNotif = null;
            }, 300);
        }, 4000);
    }

    async function ejecutarCaptura() {
        animarFlash();
        reproducirSonido("foto");

        if (btnCapturarFoto) {
            btnCapturarFoto.disabled = true;
        }
        if (textoBtnFoto) {
            textoBtnFoto.textContent = "Guardando...";
        }

        try {
            const respuesta = await fetch("/api/capture", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            });

            const datos = await respuesta.json();

            if (respuesta.ok && datos.status === "ok") {
                mostrarNotificacionFoto(datos.archivo, datos.url);
            } else {
                alert(`Error al guardar la foto: ${datos.mensaje || "Error desconocido"}`);
            }
        } catch (error) {
            console.error("Error al capturar la fotografía:", error);
            alert("No se pudo conectar con el servidor para guardar la fotografía.");
        } finally {
            if (btnCapturarFoto) {
                btnCapturarFoto.disabled = false;
            }
            if (textoBtnFoto) {
                textoBtnFoto.textContent = "Sacar Foto";
            }
        }
    }

    function cancelarConteo() {
        if (temporizadorIntervalo) {
            clearInterval(temporizadorIntervalo);
            temporizadorIntervalo = null;
        }
        if (overlayConteo) {
            overlayConteo.style.display = "none";
        }
        if (btnCancelarFoto) {
            btnCancelarFoto.style.display = "none";
        }
        if (btnCapturarFoto) {
            btnCapturarFoto.style.display = "flex";
            btnCapturarFoto.disabled = false;
        }
        if (textoBtnFoto) {
            textoBtnFoto.textContent = "Sacar Foto";
        }
    }

    function iniciarCaptura() {
        if (temporizadorIntervalo) {
            return; // Ya hay un conteo en curso
        }

        if (temporizadorSegundos <= 0) {
            ejecutarCaptura();
            return;
        }

        let restante = temporizadorSegundos;
        if (overlayConteo) overlayConteo.style.display = "flex";
        if (numeroConteo) numeroConteo.textContent = restante;
        if (btnCancelarFoto) {
            btnCancelarFoto.style.display = "block";
            if (segundosRestantes) segundosRestantes.textContent = restante;
        }
        if (btnCapturarFoto) {
            btnCapturarFoto.style.display = "none";
        }

        reproducirSonido("conteo");

        temporizadorIntervalo = setInterval(() => {
            restante--;
            if (restante > 0) {
                if (numeroConteo) numeroConteo.textContent = restante;
                if (segundosRestantes) segundosRestantes.textContent = restante;
                reproducirSonido("conteo");
            } else {
                clearInterval(temporizadorIntervalo);
                temporizadorIntervalo = null;

                if (overlayConteo) overlayConteo.style.display = "none";
                if (btnCancelarFoto) btnCancelarFoto.style.display = "none";
                if (btnCapturarFoto) {
                    btnCapturarFoto.style.display = "flex";
                }

                ejecutarCaptura();
            }
        }, 1000);
    }

    if (btnCapturarFoto) {
        btnCapturarFoto.addEventListener("click", iniciarCaptura);
    }

    if (btnCancelarFoto) {
        btnCancelarFoto.addEventListener("click", cancelarConteo);
    }

    // --------------------------------------------------------------------------
    // Módulo de Galería y Visor Lightbox
    // --------------------------------------------------------------------------
    const btnVerGaleria = document.getElementById("btnVerGaleria");
    const modalGaleria = document.getElementById("modalGaleria");
    const modalFondo = document.getElementById("modalFondo");
    const btnCerrarGaleria = document.getElementById("btnCerrarGaleria");
    const badgeTotalFotos = document.getElementById("badgeTotalFotos");
    const contenedorFotosGaleria = document.getElementById("contenedorFotosGaleria");

    const lightboxVisor = document.getElementById("lightboxVisor");
    const lightboxFondo = document.getElementById("lightboxFondo");
    const btnCerrarLightbox = document.getElementById("btnCerrarLightbox");
    const imgLightbox = document.getElementById("imgLightbox");
    const nombreLightbox = document.getElementById("nombreLightbox");
    const btnDescargarLightbox = document.getElementById("btnDescargarLightbox");

    function abrirModalGaleria() {
        if (!modalGaleria) return;
        modalGaleria.style.display = "flex";
        cargarGaleria();
    }

    function cerrarModalGaleria() {
        if (!modalGaleria) return;
        modalGaleria.style.display = "none";
    }

    function abrirLightbox(url, filename) {
        if (!lightboxVisor || !imgLightbox) return;
        imgLightbox.src = url;
        if (nombreLightbox) nombreLightbox.textContent = filename;
        if (btnDescargarLightbox) {
            btnDescargarLightbox.href = url;
            btnDescargarLightbox.download = filename;
        }
        lightboxVisor.style.display = "flex";
    }

    function cerrarLightbox() {
        if (!lightboxVisor) return;
        lightboxVisor.style.display = "none";
        if (imgLightbox) imgLightbox.src = "";
    }

    async function cargarGaleria() {
        if (!contenedorFotosGaleria) return;
        contenedorFotosGaleria.innerHTML = `
            <div class="galeria-vacia">
                <p>Cargando fotografías...</p>
            </div>
        `;

        try {
            const res = await fetch("/api/photos");
            const data = await res.json();

            if (!data.photos || data.photos.length === 0) {
                if (badgeTotalFotos) badgeTotalFotos.textContent = "0 fotos";
                contenedorFotosGaleria.innerHTML = `
                    <div class="galeria-vacia">
                        <div class="galeria-vacia-icono">📷</div>
                        <p>No hay fotografías guardadas todavía.</p>
                        <small style="color: #8d8d99;">Toma una fotografía usando el botón "Sacar Foto".</small>
                    </div>
                `;
                return;
            }

            if (badgeTotalFotos) {
                badgeTotalFotos.textContent = `${data.photos.length} ${data.photos.length === 1 ? "foto" : "fotos"}`;
            }

            let html = '<div class="galeria-grid">';
            data.photos.forEach(foto => {
                html += `
                    <div class="tarjeta-foto" id="card-${foto.filename}">
                        <div class="foto-thumb-contenedor" data-url="${foto.url}" data-filename="${foto.filename}" title="Clic para ampliar">
                            <img class="foto-thumb" src="${foto.url}" alt="${foto.filename}" loading="lazy" />
                            <div class="foto-overlay-zoom">🔍</div>
                        </div>
                        <div class="foto-meta">
                            <span class="foto-nombre" title="${foto.filename}">${foto.filename}</span>
                            <div class="foto-subinfo">
                                <span>${foto.fecha}</span>
                                <span>${foto.tamano_kb} KB</span>
                            </div>
                        </div>
                        <div class="foto-acciones">
                            <a href="${foto.url}" download="${foto.filename}" class="btn-accion-foto" title="Descargar foto">
                                ⬇ Descargar
                            </a>
                            <button type="button" class="btn-accion-foto btn-eliminar-foto" data-filename="${foto.filename}" title="Eliminar foto">
                                🗑️
                            </button>
                        </div>
                    </div>
                `;
            });
            html += '</div>';

            contenedorFotosGaleria.innerHTML = html;
        } catch (error) {
            console.error("Error al cargar galería:", error);
            contenedorFotosGaleria.innerHTML = `
                <div class="galeria-vacia">
                    <p style="color: #e57878;">Error al cargar las fotografías del servidor.</p>
                </div>
            `;
        }
    }

    async function eliminarFoto(filename) {
        if (!confirm(`¿Deseas eliminar la fotografía ${filename}?`)) {
            return;
        }

        try {
            const res = await fetch(`/api/photos/${encodeURIComponent(filename)}`, {
                method: "DELETE"
            });
            const data = await res.json();
            if (res.ok && data.status === "ok") {
                cargarGaleria();
            } else {
                alert(`Error al eliminar: ${data.mensaje || "Desconocido"}`);
            }
        } catch (error) {
            console.error("Error al eliminar foto:", error);
            alert("No se pudo conectar con el servidor para eliminar la fotografía.");
        }
    }

    // Delegación de eventos para la galería
    if (contenedorFotosGaleria) {
        contenedorFotosGaleria.addEventListener("click", (e) => {
            const thumb = e.target.closest(".foto-thumb-contenedor");
            if (thumb) {
                const url = thumb.dataset.url;
                const filename = thumb.dataset.filename;
                abrirLightbox(url, filename);
                return;
            }

            const btnEliminar = e.target.closest(".btn-eliminar-foto");
            if (btnEliminar) {
                const filename = btnEliminar.dataset.filename;
                eliminarFoto(filename);
                return;
            }
        });
    }

    if (btnVerGaleria) {
        btnVerGaleria.addEventListener("click", abrirModalGaleria);
    }
    if (btnCerrarGaleria) {
        btnCerrarGaleria.addEventListener("click", cerrarModalGaleria);
    }
    if (modalFondo) {
        modalFondo.addEventListener("click", cerrarModalGaleria);
    }

    if (btnCerrarLightbox) {
        btnCerrarLightbox.addEventListener("click", cerrarLightbox);
    }
    if (lightboxFondo) {
        lightboxFondo.addEventListener("click", cerrarLightbox);
    }

    // Soporte para tecla Escape en modales
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (lightboxVisor && lightboxVisor.style.display !== "none") {
                cerrarLightbox();
            } else if (modalGaleria && modalGaleria.style.display !== "none") {
                cerrarModalGaleria();
            }
        }
    });

    // Inicializar estado de bloqueo según la cámara y sobreposición al cargar
    const camaraInicial = document.querySelector('input[name="camara"]:checked')?.value || "rgb";
    actualizarEstadoCamara(camaraInicial);
});

