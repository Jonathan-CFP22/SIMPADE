// Lógica de cálculo por fila (se mantiene igual a la anterior)
   function calcularFila(fila) {
    // --- Cálculo de Porcentaje de Notas ---
    let totalEvaluados = 0; 
    let aprobados = 0;
    const selectsNotas = fila.querySelectorAll('select[name*="inf_"], select[name*="tp_final_"]');
    const inputPorcTotal = fila.querySelector('input[name*="porc_notas_"]');
    const spanPorc = fila.querySelector('.info_porc_visual');

    selectsNotas.forEach(select => {
        if (select.value !== "") {
            totalEvaluados++;
            if (parseInt(select.value) >= 4) aprobados++;
        }
    });

    let porcentaje = totalEvaluados > 0 ? (aprobados / totalEvaluados) * 100 : 0;
    spanPorc.innerHTML = porcentaje.toFixed(2) + "%";
    inputPorcTotal.value = porcentaje.toFixed(2);

    // --- Cálculo de Porcentaje Cualitativo (EL QUE FALLABA) ---
    const cualitativos = fila.querySelectorAll('.select-cualitativo');
    const inputCualitativo = fila.querySelector('input[name*="porc_cualit_"]'); // Nombre corregido
    const spanCualitativo = fila.querySelector('.total_text_visual');
    let respuestasSi = 0;

    cualitativos.forEach(select => { 
        if (select.value === "SI") respuestasSi++; 
    });

    // Dividimos siempre por 3 (o la cantidad de selects cualitativos)
    let porcCuali = (respuestasSi / cualitativos.length) * 100;
    spanCualitativo.innerHTML = porcCuali.toFixed(0) + "%";
    inputCualitativo.value = porcCuali.toFixed(2);
}

    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('form-select')) {
            const fila = e.target.closest('tr');
            if (fila) calcularFila(fila);
        }
    });