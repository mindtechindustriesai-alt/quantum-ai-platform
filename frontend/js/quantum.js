/**
 * QUANTUM AI — Quantum Status & Verification
 * Fetches CHSH data from backend and displays badge
 */

// ============================================================
// QUANTUM CONSTANTS (Fallback)
// ============================================================

const QUANTUM_DATA = {
    chsh_s: 2.76,
    classical_limit: 2.0,
    quantum_max: 2.828,
    percent_above_classical: 38.0,
    correlation: 0.984,
    patent: 'SA 2026/05142',
    verification_date: '2026-06-25',
    ibm_job_id: 'd8uhvl4bp3hs738628cg',
    text: 'CHSH S=2.76 · 38% above classical'
};

// ============================================================
// FETCH FROM BACKEND
// ============================================================

async function fetchQuantumData() {
    const backendUrl = localStorage.getItem('backendUrl') || 'https://quantum-ai-backend.onrender.com';
    
    try {
        const response = await fetch(`${backendUrl}/api/quantum/status`);
        if (response.ok) {
            const data = await response.json();
            return { ...QUANTUM_DATA, ...data };
        }
        return QUANTUM_DATA;
    } catch (error) {
        console.warn('Quantum backend offline, using cached data');
        return QUANTUM_DATA;
    }
}

// ============================================================
// UPDATE UI
// ============================================================

async function updateQuantumBadge() {
    const data = await fetchQuantumData();
    const badge = document.getElementById('quantumBadge');
    if (badge) {
        badge.innerHTML = `
            <i class="fas fa-shield-alt"></i>
            <span>CHSH S=${data.chsh_s} · ${Math.round(data.correlation * 100)}% · ${data.patent}</span>
        `;
    }
    return data;
}

// ============================================================
// GET QUANTUM CONFIDENCE
// ============================================================

function getQuantumConfidence(signalConfidence) {
    // Quantum confidence = signal confidence × quantum correlation
    const quantumCorrelation = QUANTUM_DATA.correlation;
    return Math.round(signalConfidence * quantumCorrelation);
}

// ============================================================
// EXPOSE
// ============================================================

window.QUANTUM_DATA = QUANTUM_DATA;
window.fetchQuantumData = fetchQuantumData;
window.updateQuantumBadge = updateQuantumBadge;
window.getQuantumConfidence = getQuantumConfidence;

// Auto-update on load
document.addEventListener('DOMContentLoaded', () => {
    updateQuantumBadge();
    console.log('⚛️ Quantum AI · CHSH S=2.76 · 38% above classical');
    console.log(`   Patent: ${QUANTUM_DATA.patent}`);
    console.log(`   IBM Job: ${QUANTUM_DATA.ibm_job_id}`);
});
