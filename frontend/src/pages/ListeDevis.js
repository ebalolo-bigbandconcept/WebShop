import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

function ListeDevis() {
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate();
  const [devis, setDevis] = useState([])

  // ### Fetch all devis from all clients from the backend ###
  const getEveryDevis = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/all-devis`)
      .then((resp) => {
        setDevis(resp.data.data);
        console.log(resp.data.data)
        setLoading(false);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error !== "Aucun clients trouvé") {
            alert(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue.");
        }
      });
  };

  useEffect(() => {
    getEveryDevis();
  }, []);
  
  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Liste des devis</h1>
      <table className="table table-hover table-striped">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Client</th>
            <th scope="col">Devis</th>
            <th scope="col">Description</th>
            <th scope="col">Date</th>
            <th scope="col">Montant HT</th>
            <th scope="col">Montat TVA</th>
            <th scope="col">Montant TTC</th>
            <th scope="col">Statut</th>
          </tr>
        </thead>
        <tbody>
          {devis !== undefined ? (
            devis.map((devis) => (
              <tr key={devis.id} onClick={() => {navigate({ pathname: `/devis/${devis.client.id}/${devis.id}`});}}>
                <td>{devis.id}</td>
                <td>{devis.client.nom} {devis.client.prenom}</td>
                <td>{devis.titre}</td>
                <td>{devis.description}</td>
                <td>{devis.date}</td>
                <td>{devis.montant_HT}</td>
                <td>{devis.montant_TVA}</td>
                <td>{devis.montant_TTC}</td>
                <td>{devis.statut}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={9}>Aucun devis trouvé</td>
            </tr>
            )}
        </tbody>
      </table>
    </div>
  );
  }
export default ListeDevis;