import { useParams } from "react-router";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

function Devis() {
  const { id_client, id_devis } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const today = new Date().toISOString().split('T')[0];

  const [devis, setDevis] = useState(null);
  const [client, setClient] = useState(null);
  const [articles, setArticles] = useState(null);

  const [article_selected, setArticleSelected] = useState(null);
  const [article_quantity, setArticleQuantity] = useState(1);
  const [articles_in_devis, setArticlesInDevis] = useState([]);

  const [form_submited, setFormSubmited] = useState(false);
  const [devis_title, setDevisTitle] = useState("");
  const [devis_description, setDevisDescription] = useState("");
  const [devis_date, setDevisDate] = useState(today);
  const [devis_montant_HT, setDevisMontantHT] = useState(0);
  const [devis_montant_TVA, setDevisMontantTVA] = useState(0);
  const [devis_montant_TTC, setDevisMontantTTC] = useState(0);
  const [devis_status, setDevisStatus] = useState("Non payé");

  const [devis_title_error, setDevisTitleError] = useState("");
  const [devis_description_error, setDevisDescriptionError] = useState("");
  const [devis_date_error, setDevisDateError] = useState("");

  const [article_quantity_error, setArticleQuantityError] = useState("");

  const [isNewDevis, setIsNewDevis] = useState(false);

  // ### User input validation ###
  const devisTitleVerif = async (value) => {
    if (value === "") {
      setDevisTitleError("Veuillez entrer un nom d'article");
      return false;
    }
    setDevisTitleError("");
    return true;
  }

  const devisDescriptionVerif = async (value) => {
    if (value === "") {
      setDevisDescriptionError("Veuillez entrer une description");
      return false;
    }
    setDevisDescriptionError("");
    return true;
  }

  const devisDateVerif = async (value) => {
    if (value === "") {
      setDevisDateError("Veuillez entrer une date");
      return false;
    }
    else if (value < today) {
      setDevisDateError("Veuillez entrer une date valide");
    }
    setDevisDateError("");
    return true;
  }

  const devisContentVerif = async (articles) => {
    if (articles.length === 0) {
      alert("Veuillez ajouter au moins un article au devis.");
      return false;
    }
    return true;
  }

  const articleQuantityVerif = async (value) => {
    if (value <= 0) {
      setArticleQuantityError("Veuillez entrer une quantité valide");
      return false;
    }
    setArticleQuantityError("");
    return true;
  }

  // ### Handle modal ###
  const showModal = () => {
      const popup = document.getElementById("popup");
      const modal = new bootstrap.Modal(popup, {});
      modal.show();
    }

  const handleAddArticle = () => {
    showModal();
  }

  const handleClose = () => {
    const popup = document.getElementById("popup");
    const modal = bootstrap.Modal.getInstance(popup);
    modal.hide();

    setArticleQuantity(1);
    setArticleSelected(null);
    setArticleQuantityError("");
    console.log(articles_in_devis);
  }

  // ### Add new article to devis ###
  
  const addNewArticle = async () => {
    const isQuantityValid = articleQuantityVerif(article_quantity);
    const isArticleSelected = article_selected !== null;

    // If article is not already in the devis
    if (articles_in_devis.find(article => article.id === article_selected.id)) {
      alert("Cet article est déjà dans le devis.");
      return;
    }

    // Set article in devis if inputs are valid
    if (isQuantityValid && isArticleSelected) {
      const newArticle = {
        ...article_selected,
        quantité: article_quantity,
        montant_HT: (article_selected.prix_vente_HT * article_quantity).toFixed(2),
        montant_TVA: ((article_selected.prix_vente_HT * article_selected.taux_tva.taux) * article_quantity).toFixed(2),
        montant_TTC: ((article_selected.prix_vente_HT * (1 + article_selected.taux_tva.taux)) * article_quantity).toFixed(2),
      };

      // Update devis totals
      setDevisMontantHT((prevMontant) => (parseFloat(prevMontant) + parseFloat(newArticle.montant_HT)).toFixed(2));
      setDevisMontantTVA((prevMontant) => (parseFloat(prevMontant) + parseFloat(newArticle.montant_TVA)).toFixed(2));
      setDevisMontantTTC((prevMontant) => (parseFloat(prevMontant) + parseFloat(newArticle.montant_TTC)).toFixed(2));

      setArticlesInDevis((prevArticles) => [...prevArticles, newArticle]);
      handleClose();
    }
  }

  // ### Save devis to database ###
  const saveDevis = async () => {
    setFormSubmited(true);
    const isTitleValid = devisTitleVerif(devis_title);
    const isDescriptionValid = devisDescriptionVerif(devis_description);
    const isDateValid = devisDateVerif(devis_date);
    const isContentValid = devisContentVerif(articles_in_devis);

    const isformValid = isTitleValid && isDescriptionValid && isDateValid && isContentValid;

    if (isformValid){
      const devisData = {
        title: devis_title,
        description: devis_description,
        date: devis_date,
        montant_HT: devis_montant_HT,
        montant_TVA: devis_montant_TVA,
        montant_TTC: devis_montant_TTC,
        status: devis_status,
        client_id: id_client,
        articles: articles_in_devis.map(article => ({
          article_id: article.id,
          quantité: article.quantité,
        })),
      };

      if (isNewDevis) {
        // Create new devis
        httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/create-devis`, devisData)
        .then((resp) => {
          console.log(resp);
          navigate(`/admin/clients/${id_client}`);
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            console.log(error.response.data.error);
          } else {
            alert("Une erreur est survenue lors de la création du devis.");
          }
        });
      } else {
        // Update existing devis
        httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/update-devis/${id_devis}`, devisData)
        .then((resp) => {
          alert("Devis mis à jour avec succès.");
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            console.log(error.response.data.error);
          } else {
            alert("Une erreur est survenue lors de la mise à jour du devis.");
          }
        });
      }
    }
  }

  // ### Fetch devis, client info and every articles on page load ###
  const getDevisInfo = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/devis-info/${id_devis}`)
      .then((resp) => {
        setDevis(resp.data);
        console.log(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.status === 404) {
            setIsNewDevis(true);
          }else{
            alert(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  const getClientInfo = async () => {
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
  }

  const getAllArticles = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/@all-articles`)
      .then((resp) => {
        setArticles(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  useEffect(() => {
    getDevisInfo();
    getClientInfo();
    getAllArticles();
  }, []);

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
      <h3 className="text-end mt-4">Montant total TTC: {devis_montant_TTC} €</h3>
      <table className="table table-hover table-striped mt-4">
        <thead>
          <tr>
            <th scope="col">Article</th>
            <th scope="col">Quantité</th>
            <th scope="col">Montant u. HT</th>
            <th scope="col">Montant u. TVA</th>
            <th scope="col">Montant u. TTC</th>
          </tr>
        </thead>
        <tbody>
          {articles_in_devis.length > 0 ? (
            articles_in_devis.map((article) => (
              <tr key={article.id}>
                <td>{article.nom}</td>
                <td>{article.quantité}</td>
                <td>{article.montant_HT} €</td>
                <td>{article.montant_TVA} €</td>
                <td>{article.montant_TTC} €</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={6}>Aucun articles</td>
            </tr>
            )}
        </tbody>
      </table>
      <div className="d-flex justify-content-between">
        <button className="btn btn-primary" onClick={handleAddArticle}>+ Ajouter un article</button>
        <button className="btn btn-success" onClick={saveDevis}> Enregistrer le devis</button>
      </div>
      <div className="modal fade" id="popup" tabIndex="-1">
        <div className="modal-dialog modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h1 className="modal-title fs-5" id="popupLabel">Ajouter un article</h1>
            </div>
            <div className="modal-body">
              <table className="table table-hover table-striped mt-4">
                <thead>
                  <tr>
                    <th scope="col">Article</th>
                    <th scope="col">Description</th>
                    <th scope="col">Montant u. HT</th>
                  </tr>
                </thead>
                <tbody>
                  {articles !== null && articles !== undefined ? (
                    articles.data.map((article) => (
                      <tr key={article.id} onClick={() => {setArticleSelected(article);}}>
                        <td>{article.nom}</td>
                        <td>{article.description}</td>
                        <td>{article.prix_vente_HT}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6}>Aucun articles</td>
                    </tr>
                    )}
                </tbody>
                </table>
              <form className="row">
                <div className="col-5"/>
                <div className="form-outline col-2">
                  <label className="form-label">Quantité</label>
                  <input type="number" id="quantité" value={article_quantity} onChange={(e) => {setArticleQuantity(e.target.value);articleQuantityVerif(e.target.value);}}
                    className={`form-control form-control-lg ${article_quantity_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer une quantité."/>
                  <div className="invalid-feedback">{article_quantity_error}</div>
                </div>
                <div className="col-5"/>
              </form>
            </div>
            <div className="modal-footer d-flex justify-content-between">
              <button className="btn btn-lg btn-danger" onClick={handleClose}>Annuler</button>
              <button className="btn btn-lg btn-success" onClick={addNewArticle}>Ajouter</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
export default Devis;