// static/js/security.js

window.addEventListener("pageshow", function (event) {
    // Detectar si la página se cargó desde la memoria caché (Botón Atrás/Adelante)
    var historyTraversal = event.persisted || 
                           (typeof window.performance != "undefined" && 
                            window.performance.navigation.type === 2);
                            
    if (historyTraversal) {
        // Si es así, forzar una recarga real con el servidor
        window.location.reload();
    }
});