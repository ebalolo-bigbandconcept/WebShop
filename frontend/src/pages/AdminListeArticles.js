import { useParams } from "react-router";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

function ListeArticles() {
  const [loading, setLoading] = useState(true);

  const [articles, setArticles] = useState([]);

  const [form_submited, setFormSubmited] = useState(false);
  const [article_nom, setArticleNom] = useState(null);
  const [article_description, setArticleDescription] = useState(null);
  const [article_prix_achat_HT, setArticlePrixAchatHT] = useState(null);
  const [article_prix_vente_HT, setArticlePrixVenteHT] = useState(null);
  const [article_taux_tva, setArticleTauxTVA] = useState(0.20);

  const [article_id, setArticleId] = useState("");
  const [article_nom_error, setArticleNomError] = useState("");
  const [article_description_error, setArticleDescriptionError] = useState("");
  const [article_prix_achat_HT_error, setArticlePrixAchatHTError] = useState("");
  const [article_prix_vente_HT_error, setArticlePrixVenteHTError] = useState("");

  // Set modal mode
  const [MODIFY, setMODIFY] = useState(false);
  const [DELETE, setDELETE] = useState(false);
  const [CREATE, setCREATE] = useState(false);
  
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

  const prixRegex = /^\d+([.]\d{1,2})?$/;

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

  const showModal = () => {
    const popup = document.getElementById("popup");
    const modal = new bootstrap.Modal(popup, {});
    modal.show();
  }

  const handleCreateArticle = () => {
    setCREATE(true);
    setMODIFY(false);
    setDELETE(false);
    showModal();
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
      console.log(article_taux_tva);
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/articles/create`, {
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
            if (error.response.status === 400) {
              alert(error.response.data.error);
            }
          } else {
            alert("Une erreur est survenue.");
          }
        });
    }
  }

  const handleModifyArticle = async (article_id) => {
    setMODIFY(true);
    setCREATE(false);
    setDELETE(false);
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/articles/info/${article_id}`)
      .then((resp) => {
        setArticleId(resp.data.id);
        setArticleNom(resp.data.nom);
        setArticleDescription(resp.data.description);
        setArticlePrixAchatHT(resp.data.prix_achat_HT);
        setArticlePrixVenteHT(resp.data.prix_vente_HT);
        setArticleTauxTVA(resp.data.taux_tva.taux);
        console.log(resp.data);
        showModal();
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  const modifyArticle = async () => {
    setFormSubmited(true);

    const isArticleNomValid = articleNomVerif(article_nom);
    const isArticleDescriptionValid = articleDescriptionVerif(article_description);
    const isArticlePrixAchatHTValid = articlePrixAchatHTVerif(article_prix_achat_HT);
    const isArticlePrixVenteHTValid = articlePrixVenteHTVerif(article_prix_vente_HT);

    const isFormValid = isArticleNomValid && isArticleDescriptionValid && isArticlePrixAchatHTValid && isArticlePrixVenteHTValid;

    if (isFormValid) {
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/articles/update/${article_id}`, {
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
            if (error.response.status !== 400) {
              alert(error.response.data.error);
            }
          } else {
            alert("Une erreur est survenue.");
          }
        });
    }
  }

  const handleDeleteArticle = async (article_id) => {
    setDELETE(true);
    setCREATE(false);
    setMODIFY(false);
  }

  const deleteArticle = async () => {
    httpClient
      .post(`${process.env.REACT_APP_BACKEND_URL}/articles/delete/${article_id}`)
      .then((resp) => {
        console.log(resp);
        handleClose();
        getAllArticles();
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.status !== 400) {
            alert(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  const getAllArticles = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/articles/all`)
      .then((resp) => {
        setArticles(resp.data.data);
        console.log(resp.data.data);
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

  const handleClose = () => {
    // Close modal
    const popup = document.getElementById("popup");
    const modal = bootstrap.Modal.getInstance(popup);
    if (modal){
      modal.hide();
    }
    // Close modal residues
    const backdrops = document.querySelectorAll(".modal-backdrop");
    backdrops.forEach((b) => b.remove());

    document.body.classList.remove("modal-open");
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
    // Reset form
    setFormSubmited(false);
    setArticleNom("");
    setArticleDescription("");
    setArticlePrixAchatHT("");
    setArticlePrixVenteHT("");
    setArticleTauxTVA(0.20);

    setArticleNomError("");
    setArticleDescriptionError("");
    setArticlePrixAchatHTError("");
    setArticlePrixVenteHTError("");

    setCREATE(false);
    setMODIFY(false);
    setDELETE(false);
  };

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
                <h1 className="modal-title fs-5" id="popupLabel">
                  {CREATE ? 'Ajouter un nouvel article.'
                  : MODIFY ? 'Modifier l\'article.'
                  : DELETE ? 'Supprimer l\'article.' : ''}
                </h1>
              </div>
              <div className="modal-body">
                {DELETE ? <h5>Êtes-vous sûr de vouloir supprimer l'article "{article_nom}" ?</h5>
                : 
                <form className="row">
                  <div className="form-outline col-12">
                    <label className="form-label">Article</label>
                    <input type="text" id="article" value={article_nom} onChange={(e) => {setArticleNom(e.target.value);articleNomVerif(e.target.value);}}
                      className={`form-control form-control-lg ${article_nom_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un nom d'article"/>
                    <div className="invalid-feedback">{article_nom_error}</div>
                  </div>
                  <div className="form-outline col-12 mt-4">
                    <label className="form-label">Description</label>
                    <textarea id="prénom" value={article_description} onChange={(e) => {setArticleDescription(e.target.value);articleDescriptionVerif(e.target.value);}}
                      className={`form-control form-control-lg ${article_description_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer une description"/>
                    <div className="invalid-feedback">{article_description_error}</div>
                  </div>
                  <div className="form-outline col-lg-5 col-4 mt-4">
                    <label className="form-label">Prix d'achat HT</label>
                    <input type="text" id="adresse" value={article_prix_achat_HT} onChange={(e) => {
                      const value = e.target.value.replace(',', '.');
                      setArticlePrixAchatHT(value);
                      articlePrixAchatHTVerif(value);}} 
                      className={`form-control form-control-lg ${article_prix_achat_HT_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="10,00€"/>
                    <div className="invalid-feedback">{article_prix_achat_HT_error}</div>
                  </div>
                  <div className="form-outline col-lg-5 col-4 mt-4">
                    <label className="form-label">Prix de vente HT</label>
                    <input type="text" id="ville" value={article_prix_vente_HT} onChange={(e) => {
                      const value = e.target.value.replace(',', '.');
                      setArticlePrixVenteHT(value);
                      articlePrixVenteHTVerif(value);}}
                      className={`form-control form-control-lg ${article_prix_vente_HT_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="20,00€"/>
                    <div className="invalid-feedback">{article_prix_vente_HT_error}</div>
                  </div>
                  <div className="form-outline col-lg-2 col-4 mt-4">
                    <label className="form-label">TVA</label>
                    <select id="taux_tva" value={article_taux_tva} onChange={(e) => setArticleTauxTVA(e.target.value)} className={`form-control form-control-lg`}>
                      <option value={0.20}>20%</option>
                    </select>
                  </div>
                </form>
                }
              </div>
              <div className="modal-footer">
                {CREATE ? 
                  <div className="d-flex justify-content-between w-100">
                    <button className="btn btn-lg btn-danger" onClick={handleClose}>Annuler</button>
                    <button className="btn btn-lg btn-success" onClick={addNewArticle}>Ajouter</button>
                  </div>
                : MODIFY ?
                  <div className="d-flex justify-content-between w-100">
                    <button className="btn btn-lg btn-danger" onClick={handleDeleteArticle}>Supprimer</button>
                    <button className="btn btn-lg btn-success" onClick={modifyArticle}>Modifier</button>
                  </div>
                : DELETE ? 
                <div className="d-flex justify-content-center w-100">
                  <button className="btn btn-lg btn-danger me-4" onClick={handleClose}>Non</button>
                  <button className="btn btn-lg btn-primary" onClick={deleteArticle}>Oui</button>
                </div> : ''
                }
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
          {articles.length > 0 ? (
            articles.map((article) => (
              <tr key={article.id} onClick={() => {handleModifyArticle(article.id)}}>
                <td>{article.id}</td>
                <td>{article.nom}</td>
                <td>{article.description}</td>
                <td>{article.prix_achat_HT} €</td>
                <td>{article.prix_vente_HT} €</td>
                <td>{article.taux_tva.taux * 100} %</td>
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
      <button className="btn btn-primary" onClick={handleCreateArticle}>+ Ajouter un nouvel article</button>
    </div>
  );
}
export default ListeArticles;