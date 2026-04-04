<?php
// Aumentar el tiempo de ejecución permitido
set_time_limit(600);
// Configuración
$path = "/var/www/escobar"; // Ruta real de tu proyecto
$secret = "qweASD*+*36741506"; // Una clave que tú inventes
$output = shell_exec("cd $path && git pull origin main 2>&1");
file_put_contents("deploy_log.txt", date('Y-m-d H:i:s') . " - " . $output . "\n", FILE_APPEND);
echo "Proceso completado. Revisa el log si hubo errores.";
$branch = "master"; // La rama que quieres desplegar

// 1. Obtener la firma de GitHub
$signature = $_SERVER['HTTP_X_HUB_SIGNATURE'] ?? null;

// 2. VALIDACIÓN: Solo validamos si existe la firma (Petición de GitHub)
if ($signature) {
    $payload = file_get_contents('php://input');
    $parts = explode('=', $signature, 2);
    
    if (count($parts) < 2) {
        die("Firma mal formateada");
    }

    $algo = $parts[0];
    $hash = $parts[1];

    if ($hash !== hash_hmac($algo, $payload, $secret)) {
        die("Firma inválida. Acceso denegado.");
    }
} else {
    // 3. MODO MANUAL: Si lo corres tú por terminal, avisamos pero seguimos
    echo "--- Ejecución Manual Detectada (Sin firma de GitHub) ---\n";
}

// 4. EJECUCIÓN DEL DESPLIEGUE
echo "Iniciando actualización en: $path\n";

// Usamos git reset --hard para asegurar que el servidor sea igual a la nube
$command = "cd $path && git fetch origin main && git reset --hard origin/main 2>&1";

exec($command, $output, $return_var);

// Mostrar el resultado de la consola
echo implode("\n", $output) . "\n";

if ($return_var === 0) {
    echo "✅ Despliegue completado con éxito.\n";
} else {
    echo "❌ Error en el despliegue (Código: $return_var).\n";
}

// Crear la carpeta tmp si no existe por algún motivo
if (!file_exists("$path/tmp")) {
    mkdir("$path/tmp", 0755, true);
}

// "Tocar" el archivo para avisar a LiteSpeed que reinicie Django
exec("touch $path/tmp/restart.txt");

echo "🚀 Aplicación reiniciada para aplicar cambios de Python.\n";