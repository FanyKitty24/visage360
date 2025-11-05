// Variable global temporal para simular el Patrón Singleton (se reemplazará por un servicio)
let G_USER_DATA = null; 
const BASE_API_URL = "/api"; // Prefijo de todas las rutas de Flask

// Función para resaltar la opción de menú activa (mantener)
function activeMenuOption(href) {
    $(".app-menu .nav-link")
        .removeClass("active")
        .removeAttr('aria-current')

    $(`[href="${(href ? href : "#/")}"]`)
        .addClass("active")
        .attr("aria-current", "page")
}

const app = angular.module("angularjsApp", ["ngRoute"])

// =========================================================================
// CONFIGURACIÓN DE RUTAS Y VISTAS (URLs limpias y nombres actualizados)
// =========================================================================
app.config(function ($routeProvider, $locationProvider) {
    $locationProvider.hashPrefix("")

    $routeProvider
        // Ruta principal: Login
        .when("/", {
            templateUrl: "/vistas/login.html", 
            controller: "LoginCtrl" // Usaremos LoginCtrl
        })
        // Ruta para ver el Historial (Lectura R)
        .when("/historial", {
            templateUrl: "/vistas/historial_analisis.html",
            controller: "HistorialAnalisisCtrl" 
        })
        // Ruta para ver el Detalle de una recomendación específica
        .when("/detalle/:analysis_id", { 
            templateUrl: "/vistas/detalle_analisis.html", 
            controller: "DetalleAnalisisCtrl" 
        })
        // Ruta para iniciar un nuevo análisis (futuro CRUD: C)
        .when("/nuevo-analisis", {
             templateUrl: "/vistas/nuevo_analisis.html", 
             controller: "AnalisisCtrl" 
        })
        .otherwise({
            redirectTo: "/"
        })
})

// =========================================================================
// RUN BLOCK (Funciones globales de AngularJS, mantiene animación/fecha)
// =========================================================================
app.run(["$rootScope", "$location", "$timeout", function($rootScope, $location, $timeout) {
    // Código de fecha/hora y animaciones del profesor (se mantiene)
    // ...
    
    // Función de chequeo de autenticación para proteger rutas
    $rootScope.$on('$routeChangeStart', function(event, next, current) {
        // Si el usuario no está logueado y la ruta no es la de Login
        if (next.$$route && next.$$route.originalPath !== '/' && !G_USER_DATA) {
            $location.path('/'); // Redirigir al login
        }
    });

    // Código de fecha/hora y animaciones del profesor (se mantiene)
    actualizarFechaHora();

    $rootScope.$on("$routeChangeSuccess", function (event, current, previous) {
        // Lógica de animación y menú activo (se mantiene)
        const path = current.$$route.originalPath;
        // ... (resto de la lógica de animación)
        activeMenuOption(`#${path}`);
    });
}])

// =========================================================================
// CONTROLADORES DE VISAGE360
// =========================================================================

// 1. Controlador para Login (Inicio de Sesión)
app.controller("LoginCtrl", function ($scope, $http, $location) {
    // Nota: El formulario HTML debe tener el ID 'frmInicioSesion'
    $("#frmInicioSesion").submit(function (event) {
        event.preventDefault();
        
        const loginData = {
            email: $("#txtEmail").val(), 
            password: $("#txtContrasena").val()
        };

        // Uso de $http para la llamada RESTful a Flask
        $http.post(BASE_API_URL + "/login", loginData)
        .then(function (response) {
            const data = response.data;

            if (data.success) {
                alert("Inicio de sesión exitoso. ¡Bienvenido/a!");
                
                // *** PATRÓN SINGLETON SIMULADO ***
                // Almacenamos los datos del usuario globalmente
                G_USER_DATA = data.user; 
                
                $location.path("/historial"); // Redirigir al historial
            } else {
                alert(data.message || "Usuario y/o Contraseña Incorrecto(s)");
            }
        })
        .catch(function (error) {
            alert("Error de conexión con la API: " + (error.data.message || error.statusText));
        });
    });
});


// 2. Controlador para Historial de Análisis (Lectura - R del CRUD)
app.controller("HistorialAnalisisCtrl", function ($scope, $http, $location) {
    
    // Función para obtener los datos del historial
    $scope.buscarHistorialAnalisis = function() {
        if (!G_USER_DATA) {
             // Si no hay datos, redirigir al login (aunque $routeChangeStart ya lo hace)
             $location.path("/"); 
             return;
        }

        const userId = G_USER_DATA.id; // Obtenemos el ID del usuario logueado (Tabla: usuarios.id)
        
        // Llamada GET al endpoint RESTful de Flask
        $http.get(BASE_API_URL + `/historial_analisis/${userId}`)
        .then(function (response) {
            const data = response.data;
            if (data.success) {
                // Asignar los datos al scope. historiales será usado por ng-repeat.
                $scope.historiales = data.historial; 
            } else {
                alert("No se pudo cargar el historial.");
                $scope.historiales = [];
            }
        })
        .catch(function (error) {
             alert("Error de conexión al cargar el historial.");
             $scope.historiales = [];
        });
    };
    
    // Función para ver el detalle de la recomendación (Lectura R detallada)
    $scope.viewDetails = function(analysisId) {
        // Redirigir a la vista de detalle, pasando el ID del análisis (Tabla: analysis_history.id_analysis)
        $location.path(`/detalle/${analysisId}`);
    };

    // Inicializa la búsqueda al cargar el controlador
    $scope.buscarHistorialAnalisis();
});


// 3. Controlador para Detalle de Análisis (Lectura R específica)
app.controller("DetalleAnalisisCtrl", function ($scope, $http, $routeParams) {
    // Obtenemos el ID de análisis de la URL (ruta: /detalle/:analysis_id)
    const analysisId = $routeParams.analysis_id; 
    
    $scope.detalle = null;
    
    $http.get(BASE_API_URL + `/analisis/detalle/${analysisId}`)
    .then(function (response) {
        const data = response.data;
        if (data.success) {
            // El 'detalle' contiene el JSON completo (resultado_json)
            $scope.detalle = data.detalle; 
        } else {
            alert("No se pudo cargar el detalle del análisis.");
        }
    })
    .catch(function (error) {
        alert("Error de conexión al obtener el detalle.");
    });
});


// Mantiene la inicialización de Luxon y el activeMenuOption
const DateTime = luxon.DateTime
let lxFechaHora

document.addEventListener("DOMContentLoaded", function (event) {
    // ... (código de configuración de fecha/hora, si es necesario)
    activeMenuOption(location.hash)
})
