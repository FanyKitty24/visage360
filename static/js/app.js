function activeMenuOption(href) {
    $(".app-menu .nav-link")
    .removeClass("active")
    .removeAttr('aria-current')

    $(`[href="${(href ? href : "#/")}"]`)
    .addClass("active")
    .attr("aria-current", "page")
}

const app = angular.module("angularjsApp", ["ngRoute"])
app.config(function ($routeProvider, $locationProvider) {
    $locationProvider.hashPrefix("")

    $routeProvider
    .when("/", {
        templateUrl: "/app",
        controller: "appCtrl"
    })
      .when("/historialanalisis", {
        templateUrl: "/historialanalisis",
        controller: "historialanalisisCtrl"
    })

    .otherwise({
        redirectTo: "/"
    })
})

app.run(["$rootScope", "$location", "$timeout", function($rootScope, $location, $timeout) {
    // ... Código del profesor para fecha/hora y animaciones (sin cambios) ...
    function actualizarFechaHora() {
        lxFechaHora = DateTime
        .now()
        .setLocale("es")

        $rootScope.angularjsHora = lxFechaHora.toFormat("hh:mm:ss a")
        $timeout(actualizarFechaHora, 1000)
    }

    $rootScope.slide = ""

    actualizarFechaHora()

    $rootScope.$on("$routeChangeSuccess", function (event, current, previous) {
        $("html").css("overflow-x", "hidden")
        
        const path = current.$$route.originalPath

        if (path.indexOf("splash") == -1) {
            const active = $(".app-menu .nav-link.active").parent().index()
            const click  = $(`[href^="#${path}"]`).parent().index()

            if (active != click) {
                $rootScope.slide  = "animate__animated animate__faster animate__slideIn"
                $rootScope.slide += ((active > click) ? "Left" : "Right")
            }

            $timeout(function () {
                $("html").css("overflow-x", "auto")

                $rootScope.slide = ""
            }, 1000)

            activeMenuOption(`#${path}`)
        }
    })
}])

// Controlador para Login
app.controller("appCtrl", function ($scope, $http) {
    $("#frmInicioSesion").submit(function (event) {
        event.preventDefault()
        $.post("/IniciarSesion", $(this).serialize(), function (respuesta) {
            if (respuesta.length) {
                alert("Iniciaste Sesión")
                window.location = "/#/usuarios"
                return
            }
            alert("Usuario y/o Contraseña Incorrecto(s)")
        })
    })
})


// Controlador para Historial Asistencias (Dirigida por Eventos)
app.controller("historialanalisisCtrl", function ($scope, $http) {
    function buscarAsistencias() {
        $.get("/tbodyHistorialAnalisis", function (trsHTML) {
            $("#tbodyHistorialAnalisis").html(trsHTML);
        });
    }
    buscarAsistencias();
    
    // Configuración de Pusher
    Pusher.logToConsole = true;
    var pusher = new Pusher("686124f7505c58418f23", { // Tu KEY
      cluster: "us2"
    });
    var channel = pusher.subscribe("canalHistorialAnalisis");
    channel.bind("eventoHistorialAnalisis", function(data) {
        buscarHistorialAnalisis();
    });

    // Botón de Editar
    $(document).on("click", ".btn-editar-historial-analisis", function () {
        const id = $(this).data("id");
        const fecha = $(this).data("fecha");
        const comentarios = $(this).data("comentarios");

        $("#txtFecha").val(fecha);
        $("#txtComentarios").val(comentarios);
        
        // CORRECCIÓN: Toda la lógica de edición (incluyendo crear el input oculto)
        // debe estar DENTRO del evento 'click'.
        if ($("#hiddenId").length === 0) {
            $("#frmHistorialAnalisis").append(`<input type="hidden" id="hiddenId" name="id_analysis">`);
        }
        $("#hiddenId").val(id);
    });

    $(document).off("submit", "#frmAsistencia").on("submit", "#frmAsistencia", function (event) {
    event.preventDefault();
    const id = $("#hiddenId").val();
    const url = id ? "/historialanalisis/editar" : "/analisis";

    $.post(url, $(this).serialize())
        .done(function () {
            buscarHistorialAnalisis();
            $("#frmHistorialAnalisis")[0].reset();
            $("#hiddenId").remove();
        })
        .fail(function () {
            alert("Hubo un error al guardar la asistencia.");
        });
    });
});

const DateTime = luxon.DateTime
let lxFechaHora

document.addEventListener("DOMContentLoaded", function (event) {
    const configFechaHora = {
        locale: "es",
        weekNumbers: true,
        minuteIncrement: 15,
        altInput: true,
        altFormat: "d/F/Y",
        dateFormat: "Y-m-d",
    }
    activeMenuOption(location.hash)
})
