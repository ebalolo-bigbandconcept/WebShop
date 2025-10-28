import { useParams } from "react-router";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

function ListeArticles() {
  const [loading, setLoading] = useState(true);

  const [articles, setArticles] = useState([]);

  const [form_submited, setFormSubmited] = useState(false);
  const [article_nom, setArticleNom] = useState("");
  const [article_description, setArticleDescription] = useState("");
  const [article_prix_achat_HT, setArticlePrixAchatHT] = useState("");
  const [article_prix_vente_HT, setArticlePrixVenteHT] = useState("");
  const [article_taux_tva, setArticleTauxTVA] = useState("");

  const [article_nom_error, setArticleNomError] = useState("");
  const [article_description_error, setArticleDescriptionError] = useState("");
  const [article_prix_achat_HT_error, setArticlePrixAchatHTError] = useState("");
  const [article_prix_vente_HT_error, setArticlePrixVenteHTError] = useState("");
  
  // ### User input validation ###
  const articleNomVerif = async (value) => {
    if (value === "") {
      setArticleNomError("Veuillez entrer un nom d'article");
      return false;
    }
    setArticleNomError("");
    return true;
  }
  
  const articleDescriptionVerif = async (value) => {
    if (value === "") {
      setArticleDescriptionError("Veuillez entrer une description");
      return false;
    }
    setArticleDescriptionError("");
    return true;
  }

  const prixRegex = /^\d+([.,]\d{1,2})?$/;

  const articlePrixAchatHTVerif = async (value) => {
    if (value === "") {
      setArticlePrixAchatHTError("Veuillez entrer un prix d'achat HT");
      return false;
    }
    else if (!prixRegex.test(value)) {
      setArticlePrixAchatHTError("Veuillez entrer un prix d'achat HT valide");
      return false;
    }
    setArticlePrixAchatHTError("");
    return true;
  }

  const articlePrixVenteHTVerif = async (value) => {
    if (value === "") {
      setArticlePrixVenteHTError("Veuillez entrer un prix de vente HT");
      return false;
    }
    else if (!prixRegex.test(value)) {
      setArticlePrixVenteHTError("Veuillez entrer un prix de vente HT valide");
      return false;
    }
    setArticlePrixVenteHTError("");
    return true;
  }

  const addNewArticle = async (e) => {
    e.preventDefault();
    setFormSubmited(true);

    const isArticleNomValid = articleNomVerif(article_nom);
    const isArticleDescriptionValid = articleDescriptionVerif(article_description);
    const isArticlePrixAchatHTValid = articlePrixAchatHTVerif(article_prix_achat_HT);
    const isArticlePrixVenteHTValid = articlePrixVenteHTVerif(article_prix_vente_HT);

    const isFormValid = isArticleNomValid && isArticleDescriptionValid && isArticlePrixAchatHTValid && isArticlePrixVenteHTValid;

    if (isFormValid) {
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/add-article`, {
          nom: article_nom,
          description: article_description,
          prix_achat_HT: article_prix_achat_HT,
          prix_vente_HT: article_prix_vente_HT,
          taux_tva: article_taux_tva,
        })
        .then((resp) => {
          console.log(resp);
          handleClose();
          getAllArticles();
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            alert(error.response.data.error);
          } else {
            alert("Une erreur est survenue.");
          }
        });
    }
  }

  const handleClose = () => {
    const popup = document.getElementById("popup");
    const modal = bootstrap.Modal.getInstance(popup);
    modal.hide();
    // Reset form
    setFormSubmited(false);
    setArticleNom("");
    setArticleDescription("");
    setArticlePrixAchatHT("");
    setArticlePrixVenteHT("");
    setArticleTauxTVA("");

    setArticleNomError("");
    setArticleDescriptionError("");
    setArticlePrixAchatHTError("");
    setArticlePrixVenteHTError("");
  };

  const getAllArticles = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/@all-articles`)
      .then((resp) => {
        setArticles(resp.data.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error === "Aucuns articles trouvé") {
          }
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  // ### Fetch all articles on page load ###
  useEffect(() => {
    getAllArticles();
    setLoading(false);
  }, []);

  if (loading) return <div>Chargement...</div>;
  
  return (
    <div>
      <h1>Liste des articles</h1>
      <br/>
      <div>
        <div className="modal fade" id="popup" tabIndex="-1">
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h1 className="modal-title fs-5" id="popupLabel">Ajouter un nouvel article.</h1>
              </div>
              <div className="modal-body">
                <form className="row">
                  <div className="form-outline col-12">
                    <label className="form-label">Article</label>
                    <input type="text" id="article" value={article_nom} onChange={(e) => {setArticleNom(e.target.value);articleNomVerif(e.target.value);}}
                      className={`form-control form-control-lg ${article_nom_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un nom d'article."/>
                    <div className="invalid-feedback">{article_nom_error}</div>
                  </div>
                  <div className="form-outline col-12 mt-4">
                    <label className="form-label">Description</label>
                    <textarea id="prénom" value={article_description} onChange={(e) => {setArticleDescription(e.target.value);articleDescriptionVerif(e.target.value);}}
                      className={`form-control form-control-lg ${article_description_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer une description."/>
                    <div className="invalid-feedback">{article_description_error}</div>
                  </div>
                  <div className="form-outline col-lg-5 col-4 mt-4">
                    <label className="form-label">Prix d'achat HT</label>
                    <input type="text" id="adresse" value={article_prix_achat_HT} onChange={(e) => {setArticlePrixAchatHT(e.target.value);articlePrixAchatHTVerif(e.target.value);}}
                      className={`form-control form-control-lg ${article_prix_achat_HT_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="10,00€"/>
                    <div className="invalid-feedback">{article_prix_achat_HT_error}</div>
                  </div>
                  <div className="form-outline col-lg-5 col-4 mt-4">
                    <label className="form-label">Prix de vente HT</label>
                    <input type="text" id="ville" value={article_prix_vente_HT} onChange={(e) => {setArticlePrixVenteHT(e.target.value);articlePrixVenteHTVerif(e.target.value);}}
                      className={`form-control form-control-lg ${article_prix_vente_HT_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="20,00€"/>
                    <div className="invalid-feedback">{article_prix_vente_HT_error}</div>
                  </div>
                  <div className="form-outline col-lg-2 col-4 mt-4">
                    <label className="form-label">TVA</label>
                    <select id="taux_tva" value={article_taux_tva} onChange={(e) => setArticleTauxTVA(e.target.value)} className={`form-control form-control-lg`}>
                      <option value="20">20%</option>
                    </select>
                  </div>
                </form>
              </div>
              <div className="modal-footer d-flex justify-content-between">
                <button className="btn btn-lg btn-danger" data-bs-dismiss="modal" onClick={handleClose}>Annuler</button>
                <button className="btn btn-lg btn-success" onClick={addNewArticle}>Enregistrer</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <table className="table table-hover table-striped">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Article</th>
            <th scope="col">Description</th>
            <th scope="col">Prix d'achat HT</th>
            <th scope="col">Prix de vente HT</th>
            <th scope="col">TVA</th>
          </tr>
        </thead>
        <tbody>
          {articles.data !== undefined ? (
            articles.data.map((article) => (
              <tr key={article.id}>
                <td>{article.id}</td>
                <td>{article.nom}</td>
                <td>{article.description}</td>
                <td>{article.prix_achat_HT}</td>
                <td>{article.prix_vente_HT}</td>
                <td>{article.taux_tva}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={6}>Aucun articles trouvé</td>
            </tr>
            )}
        </tbody>
      </table>
      <br/>
      <button className="btn btn-primary" data-bs-toggle="modal" data-bs-target="#popup">+ Ajouter un nouvel article</button>
    </div>
  );
}
export default ListeArticles;