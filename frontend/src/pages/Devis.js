import { useParams } from "react-router";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";

function Devis() {
  const { id_client, id_devis } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const today = new Date().toISOString().split('T')[0];

  const [devis, setDevis] = useState(null);
  const [client, setClient] = useState(null);
  const [articles, setArticles] = useState(null);

  const [form_submited, setFormSubmited] = useState(false);
  const [devis_title, setDevisTitle] = useState("");
  const [devis_description, setDevisDescription] = useState("");
  const [devis_date, setDevisDate] = useState(today);

  const [devis_title_error, setDevisTitleError] = useState("");
  const [devis_description_error, setDevisDescriptionError] = useState("");
  const [devis_date_error, setDevisDateError] = useState("");

  let isNewDevis = false; // Placeholder for new devis logic

  // ### User input validation ###
  const devisTitleVerif = async (value) => {

  }

  const devisDescriptionVerif = async (value) => {

  }

  const devisDateVerif = async (value) => {

  }

  // ### Fetch devis and client info on page load ###
  useEffect(() => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/devis-info/${id_devis}`)
      .then((resp) => {
        setDevis(resp.data);
        console.log(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error === "Devis non trouvé") {
            isNewDevis = true;

          }else{
            alert(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue.");
        }
      });

    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/client-info/${id_client}`)
      .then((resp) => {
        setClient(resp.data);
        setLoading(false);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }, [id_client, id_devis]);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Devis N°{id_devis}</h1>
      <br/>
      <h3>Client: {client.last_name} {client.first_name}</h3>
      <h3>Adresse: {client.street}, {client.postal_code} à {client.city}</h3>
      <form className="row">
        <div className="row">
          <div className="form-outline col-xl-4 col-6">
            <label className="form-label">Titre</label>
            <input type="text" id="titre" value={devis_title} onChange={(e) => {setDevisTitle(e.target.value);devisTitleVerif(e.target.value);}}
              className={`form-control form-control-lg ${devis_title_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un titre pour le devis."/>
            <div className="invalid-feedback">{devis_title_error}</div>
          </div>
          <div className="form-outline col-xl-2 col-6">
            <label className="form-label">Date</label>
            <input type="date" id="date" value={devis_date} onChange={(e) => {setDevisDate(e.target.value);devisDateVerif(e.target.value);}}
              className={`form-control form-control-lg ${devis_date_error ? "is-invalid" : form_submited ? "is-valid": ""}`}/>
            <div className="invalid-feedback">{devis_date_error}</div>
          </div>
        </div>
        <div className="row">
          <div className="form-outline col-xl-6 mt-4">
            <label className="form-label">Description</label>
            <textarea rows={3} id="description" value={devis_description} onChange={(e) => {setDevisDescription(e.target.value);devisDescriptionVerif(e.target.value);}}
              className={`form-control form-control-lg ${devis_description_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer une description pour le devis."/>
            <div className="invalid-feedback">{devis_description_error}</div>
          </div>
        </div>
      </form>
      <h3 className="text-end mt-4">Montant total TTC: {devis && devis.montant_TTC ? devis.montant_TTC : '0,00 €'}</h3>
      <table className="table table-hover table-striped mt-4">
        <thead>
          <tr>
            <th scope="col">Article</th>
            <th scope="col">Quantité</th>
            <th scope="col">Montant u. HT</th>
            <th scope="col">Montant u. TVA</th>
            <th scope="col">Montant u. TTC</th>
            <th scope="col">Montant total TTC</th>
          </tr>
        </thead>
        <tbody>
          {articles !== null && articles !== undefined ? (
            articles.data.map((article) => (
              <tr key={article.id} onClick={() => {navigate({ pathname: `/client/` + article.id });}}>
                <td>{article.nom}</td>
                <td>{article.nom}</td>
                <td>{article.prenom}</td>
                <td>{article.rue}, {article.code_postal} <br/> {article.ville}</td>
                <td>{article.telephone}</td>
                <td>{article.email}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={6}>Aucun articles</td>
            </tr>
            )}
        </tbody>
      </table>
    </div>
  );
}
export default Devis;