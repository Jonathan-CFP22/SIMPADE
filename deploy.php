<?php
// Configuración
$secret = "qweASD*+*36741506"; // Una clave que tú inventes
$path = "/var/www/escobar"; // Ruta real de tu proyecto
$branch = "main"; // La rama que quieres desplegar

// Validar que la petición venga de GitHub (opcional pero recomendado)
//$signature = $_SERVER['HTTP_X_HUB_SIGNATURE'] ?? '';
//if (!$signature) die("Sin firma");

$payload = file_get_contents('php://input');
list($algo, $hash) = explode('=', $signature, 2);
$payloadHash = hash_hmac($algo, $payload, $secret);

if ($hash !== $payloadHash) {
    die("Firma inválida");
}

// Ejecutar el despliegue
echo "Iniciando despliegue...\n";
exec("cd $path && git checkout $branch && git pull origin $branch 2>&1", $output);

exec("cd $path && git pull origin main 2>&1", $output);
exec("touch $path/tmp/restart.txt"); 

print_r($output);