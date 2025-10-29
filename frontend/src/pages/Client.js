import { useParams } from "react-router";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";

function Client() {
  const client_id = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  const [client, setClient] = useState("");
  const [devis, setDevis] = useState([]);

  const handleNewDevis = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/new-devis-id`)
      .then((resp) => {
        navigate({ pathname: `/devis/${client.id}/${resp.data.id}` });
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  const getClientAllDevis = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/client-devis/${client_id.id}`)
      .then((resp) => {
        setDevis(resp.data.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error !== "Aucuns devis trouvé") {
            alert(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue.");
        }
      });
  };

  const getClientInfo = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/client-info/${client_id.id}`)
      .then((resp) => {
        setClient(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  };

  // ### Fetch client all devis and info on page load ###
  useEffect(() => {
    getClientInfo();
    getClientAllDevis();
    setLoading(false);
    }, []);
  
  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <div>
        <div className="d-flex justify-content-between align-items-center">
          <h1 className="col-lg-11 col-10">Client - {client.last_name} {client.first_name}</h1>
          <button className="btn btn-danger col-lg-1 col-2" onClick={() => navigate(-1)}>Retour</button>
        </div>
        <br/>
        <table className="table table-hover table-striped">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Titre</th>
              <th scope="col">Description</th>
              <th scope="col">Date</th>
              <th scope="col">Montant HT</th>
              <th scope="col">Montant TVA</th>
              <th scope="col">Montant TTC</th>
              <th scope="col">Statut</th>
            </tr>
          </thead>
          <tbody>
            {devis.length > 0 ? (
              devis.map((devis) => (
                <tr key={devis.id} onClick={() => {navigate({ pathname: `/devis/${client.id}/${devis.id}` });}}>
                  <td>{devis.id}</td>
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
                <td colSpan={8}>Aucun devis trouvé</td>
              </tr>
            )}
          </tbody>
        </table>
        <br/>
        <button className="btn btn-primary" onClick={() => handleNewDevis()}>+ Créer un devis</button>
      </div>
    </div>
  );
  }
export default Client;