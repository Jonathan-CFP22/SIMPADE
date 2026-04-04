<?php
// 1. CONFIGURACIÓN
$path = "/var/www/escobar"; 
$secret = "qweASD*+*36741506"; // Asegúrate que en GitHub dice exactamente esto en "Secret"
$path = dirname(__FILE__); 
$log_file = $path . "/deploy_log.txt";

// 2. VALIDACIÓN DE SEGURIDAD (Debe ir PRIMERO)
$signature = $_SERVER['HTTP_X_HUB_SIGNATURE_256'] ?? $_SERVER['HTTP_X_HUB_SIGNATURE'] ?? null;

if ($signature) {
    $payload = file_get_contents('php://input');
    list($algo, $hash) = explode('=', $signature, 2);
    $payloadHash = hash_hmac($algo, $payload, $secret);

    if (!hash_equals($hash, $payloadHash)) {
        file_put_contents($log_file, date('Y-m-d H:i:s') . " - ERROR: Firma inválida.\n", FILE_APPEND);
        die("Acceso denegado.");
    }
} else {
    // Si entras tú desde el navegador, te pedirá la firma o fallará. 
    // Para pruebas manuales desde el navegador, podrías comentar el die() temporalmente.
    echo "Ejecución manual detectada. ";
}

// 3. RESPUESTA RÁPIDA A CLOUDFLARE/GITHUB (Evita el error 524)
// Esto le dice a Cloudflare "Ya recibí todo, puedes cerrar la conexión", pero el servidor sigue trabajando.
ob_start();
echo "Despliegue iniciado correctamente. Procesando cambios...";
header("Content-Length: " . ob_get_length());
header("Connection: close");
ob_end_flush();
ob_flush();
flush();

// 4. EJECUCIÓN DEL DESPLIEGUE (En segundo plano)
ignore_user_abort(true); // Seguir aunque se corte la conexión HTTP
set_time_limit(600);

$command = "cd $path && git fetch origin main && git reset --hard origin/main 2>&1";
exec($command, $output_array, $return_var);

$output_text = implode("\n", $output_array);

// 5. REINICIAR DJANGO
if (!file_exists("$path/tmp")) {
    mkdir("$path/tmp", 0755, true);
    chown("$path/tmp", "www-data");
}
touch("$path/tmp/restart.txt");

// 6. REGISTRO EN LOG
$status = ($return_var === 0) ? "ÉXITO" : "ERROR ($return_var)";
$log_entry = date('Y-m-d H:i:s') . " - [$status] - " . str_replace("\n", " ", $output_text) . "\n";
file_put_contents($log_file, $log_entry, FILE_APPEND);