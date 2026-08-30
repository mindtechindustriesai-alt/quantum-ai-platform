import numpy as np
import logging
from typing import Dict, Any, List
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.circuit.library import ZZFeatureMap
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

logger = logging.getLogger(__name__)

class QuantumFeatureEngine:
    def __init__(self, token: str = None):
        self.num_qubits = 4
        self.feature_map = ZZFeatureMap(feature_dimension=self.num_qubits, reps=2, entanglement='linear')
        self.sampler = StatevectorSampler()
        self.service = None
        
        if token:
            try:
                self.service = QiskitRuntimeService(channel="ibm_quantum", token=token)
                logger.info("IBM Quantum Runtime Service initialized successfully.")
            except Exception as e:
                logger.warning(f"Fallback to local Qiskit simulator: {e}")

    def normalize_market_data(self, price: float, volume: float, volatility: float, spread: float) -> List[float]:
        """Maps continuous market variables to the interval [-pi, pi] for quantum gate rotation."""
        features = [
            np.arctan(price) * 2,
            np.arctan(volume) * 2,
            np.arctan(volatility) * 2,
            np.arctan(spread) * 2
        ]
        return features

    def generate_quantum_signal(self, market_data: Dict[str, float]) -> Dict[str, Any]:
        """Encodes market ticks into Hilbert Space statevectors and extracts probability amplitudes."""
        try:
            raw_features = self.normalize_market_data(
                market_data.get("price", 0.0),
                market_data.get("volume", 0.0),
                market_data.get("volatility", 0.0),
                market_data.get("spread", 0.0)
            )

            # Bind market variables to circuit parameters
            bound_circuit = self.feature_map.assign_parameters(raw_features)
            bound_circuit.measure_all()

            # Execute via Sampler
            job = self.sampler.run([bound_circuit])
            result = job.result()[0]
            counts = result.data.meas.get_counts()
            
            # Calculate Quantum Expectation Value for direction
            total_shots = sum(counts.values())
            bullish_states = sum(counts.get(state, 0) for state in counts if state.startswith('1'))
            confidence = bullish_states / total_shots if total_shots > 0 else 0.5

            signal = "BUY" if confidence > 0.55 else ("SELL" if confidence < 0.45 else "HOLD")

            return {
                "signal": signal,
                "confidence": round(confidence, 4),
                "quantum_state_counts": counts,
                "status": "SUCCESS"
            }
        except Exception as e:
            logger.error(f"Quantum circuit execution error: {e}")
            return {"signal": "HOLD", "confidence": 0.0, "status": f"FAILED: {str(e)}"}

quantum_engine = QuantumFeatureEngine()
