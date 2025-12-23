import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import httpClient from "../components/httpClient";
import { useToast } from "../components/Toast";


function DevisPdfPreview() {
  const { id_client, id_devis } = useParams();
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfBlob, setPdfBlob] = useState(null);
  const navigate = useNavigate();
  const [scenario, setScenario] = useState("direct"); // "direct", "location_without_apport", "location_with_apport"
  const { showToast } = useToast();

  const handlePdf = async (selectedScenario = scenario) => {
    const params = new URLSearchParams();
    params.append("scenario", selectedScenario);
    const url = `${process.env.REACT_APP_BACKEND_URL}/devis/pdf/${id_devis}?${params.toString()}`;
    
    httpClient
      .get(url, {responseType: "blob"})
      .then((resp) => {
        if (pdfUrl) {
          URL.revokeObjectURL(pdfUrl);
        }
        const url = URL.createObjectURL(resp.data);
        setPdfBlob(resp.data);
        setPdfUrl(url);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          console.log(error.response.data.error);
        } else {
          showToast({ message: "Une erreur est survenue lors de la création du pdf.", variant: "danger" });
        }
      });
  }

  const handleScenarioChange = (newScenario) => {
    setScenario(newScenario);
    handlePdf(newScenario);
  }

  const handleSendToDocuSign = () => {
    if (!pdfBlob) {
      showToast({ message: "PDF non disponible.", variant: "warning" });
      return;
    }

    const formData = new FormData();
    formData.append("file", pdfBlob, `devis_${id_devis}.pdf`)
    
    httpClient
      .post(`${process.env.REACT_APP_BACKEND_URL}/devis/pdf/send/external/${id_client}/${id_devis}`,formData)
      .then((resp) => {
        showToast({ message: `Document envoyé ! Envelope ID: ${resp.data.envelope_id}`, variant: "success" });
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          console.log(error.response.data.error);
        } else {
          showToast({ message: "Une erreur est survenue lors de l'envoie du pdf.", variant: "danger" });
        }
      });
  }

  useEffect(() => {
    handlePdf()
  }, []);

  return (
    <div>
      <div className="d-flex w-100 justify-content-between align-items-center mb-3">
        <div className="d-flex gap-2 align-items-center">
          <label htmlFor="scenarioSelect" className="form-label mb-0 me-2">Solution:</label>
          <select
            id="scenarioSelect"
            className="form-select"
            style={{ width: "auto", display: "inline-block" }}
            value={scenario}
            onChange={(e) => handleScenarioChange(e.target.value)}
          >
            <option value="direct">Paiement direct</option>
            <option value="location_without_apport">Location sans apport</option>
            <option value="location_with_apport">Location avec apport</option>
          </select>
          <button className="btn btn-success" onClick={handleSendToDocuSign}>Envoyer le PDF</button>
        </div>
        <button className="btn btn-danger" onClick={() => navigate(`/devis/${id_client}/${id_devis}`)}>Retour</button>
      </div>
      {pdfUrl && (
        <iframe
          src={pdfUrl}
          title="Devis PDF Preview"
          width="100%"
          height="1200px"
          style={{ border: "1px solid #ccc", marginTop: "20px" }}
        ></iframe>
      )}
    </div>
  );
}

export default DevisPdfPreview;
