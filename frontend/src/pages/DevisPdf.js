import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import httpClient from "../components/httpClient";


function DevisPdfPreview() {
  const { id_client, id_devis } = useParams();
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfBlob, setPdfBlob] = useState(null);
  const navigate = useNavigate();

  const handlePdf = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/devis/pdf/${id_devis}`,{responseType: "blob"})
      .then((resp) => {
        const url = URL.createObjectURL(resp.data);
        setPdfBlob(resp.data);
        setPdfUrl(url);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          console.log(error.response.data.error);
        } else {
          alert("Une erreur est survenue lors de la création du pdf.");
        }
      });
  }

  const handleSendToDocuSign = () => {
    if(!pdfBlob) return alert("PDF non disponible.");

    // Stocker la page actuelle pour revenir après consentement
    sessionStorage.setItem("redirectAfterConsent", window.location.pathname);

    const formData = new FormData();
    formData.append("file", pdfBlob, `devis_${id_devis}.pdf`)
    
    httpClient
      .post(`${process.env.REACT_APP_BACKEND_URL}/devis/pdf/send/${id_client}`,formData)
      .then((resp) => {
        alert(`Document envoyé ! Envelope ID: ${resp.data.envelope_id}`);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error === "consent_required"){
            handleConsent()
          }else{
            console.log(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue lors de l'envoie du pdf.");
        }
      });
  }

  const handleConsent = () => {
    const clientId = process.env.REACT_APP_DOCUSIGN_CLIENT_ID;
    const redirectUri = `http://localhost:3000/consent-complete`
    const consentUrl = `https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature%20impersonation&client_id=${clientId}&redirect_uri=${redirectUri}`;
    
    window.open(consentUrl, "_blank");
  }

  useEffect(() => {
    handlePdf()
  }, []);

  return (
    <div>
      <div className="d-flex w-100 justify-content-end">
        <button className="btn btn-danger col-lg-1 col-2" onClick={() => navigate(`/devis/${id_client}/${id_devis}`)}>Retour</button>
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
      <div className="btn btn-success" onClick={handleSendToDocuSign}>Envoyer le PDF</div>
    </div>
  );
}

export default DevisPdfPreview;
