import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router";
import httpClient from "../components/httpClient";


function DevisPdfPreview() {
  const { id_client, id_devis } = useParams();
  const [pdfUrl, setPdfUrl] = useState(null);
  const navigate = useNavigate();

  const handlePdf = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/devis/pdf/${id_devis}`,{responseType: "blob"})
      .then((resp) => {
        console.log(resp)
        const url = URL.createObjectURL(resp.data);
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
    </div>
  );
}

export default DevisPdfPreview;
