import { useParams } from "react-router";
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";
import trashCan from "../assets/trash3-fill.svg";

function Devis() {
  const { id_client, id_devis } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const today = new Date().toISOString().split('T')[0];

  const [devis, setDevis] = useState(null);
  const [client, setClient] = useState(null);
  const [articles, setArticles] = useState(null);

  const [article_selected, setArticleSelected] = useState([]);
  const [article_quantite, setArticleQuantite] = useState(1);
  const [articles_in_devis, setArticlesInDevis] = useState([]);

  // Article modal pagination and filter state
  const [filteredArticles, setFilteredArticles] = useState([]);
  const [paginatedArticles, setPaginatedArticles] = useState([]);
  const [articleSearchTerm, setArticleSearchTerm] = useState("");
  const [articleCurrentPage, setArticleCurrentPage] = useState(1);
  const [articleItemsPerPage, setArticleItemsPerPage] = useState(10);

  const [form_submited, setFormSubmited] = useState(false);
  const [devis_title, setDevisTitle] = useState("");
  const [devis_description, setDevisDescription] = useState("");
  const [devis_date, setDevisDate] = useState(today);
  const [devis_montant_HT, setDevisMontantHT] = useState(0);
  const [devis_montant_TVA, setDevisMontantTVA] = useState(0);
  const [devis_montant_TTC, setDevisMontantTTC] = useState(0);
  const [devis_status, setDevisStatus] = useState("Non signé");

  const [devis_title_error, setDevisTitleError] = useState("");
  const [devis_date_error, setDevisDateError] = useState("");

  const [article_quantity_error, setArticleQuantityError] = useState("");

  const [isNewDevis, setIsNewDevis] = useState(false);

  const [DELETE, setDELETE] = useState(false);
  const [article_MODIFY, setArticleMODIFY] = useState(false);
  const [article_DELETE, setArticleDELETE] = useState(false);

  // ### User input validation ###
  const devisTitleVerif = (value) => {
    if (value === "") {
      setDevisTitleError("Veuillez entrer un nom d'article");
      return false;
    }
    setDevisTitleError("");
    return true;
  }

  const devisDateVerif = (value) => {
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

  const devisContentVerif = (articles) => {
    if (articles.length === 0) {
      alert("Veuillez ajouter au moins un article au devis.");
      return false;
    }
    return true;
  }

  const articleQuantityVerif = (value) => {
    if (value <= 0) {
      setArticleQuantityError("Veuillez entrer une quantité valide");
      return false;
    }
    setArticleQuantityError("");
    return true;
  }

  // ### Go back button ###

  const goBack = () => {
    if (location.state && location.state.from) {
      console.log(location.state.from)
      navigate(location.state.from);
    }else{
      navigate('/liste-devis');
    }
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

  const handleDeleteDevis = () => {
    setDELETE(true);
    showModal();
  }

  const handleModifyArticle = (article) => {
    setArticleSelected(article)
    setArticleQuantite(article.quantite)
    setArticleMODIFY(true);
    showModal();
  }

  const handleDeleteArticle = (article) => {
    setArticleDELETE(true);
    setArticleSelected(article)
    showModal();
  }

  const handleClose = () => {
    const popup = document.getElementById("popup");
    const modal = bootstrap.Modal.getInstance(popup);
    modal.hide();

    setArticleQuantite(1);
    setArticleSelected([]);
    setArticleQuantityError("");
    setArticleSearchTerm("");
    setArticleCurrentPage(1);
    setDELETE(false);
    setArticleMODIFY(false);
    setArticleDELETE(false);
  }

  // ### Modify selected article in devis
  const modifyArticle = () => {
    const isQuantityValid = articleQuantityVerif(article_quantite);
    
    if (isQuantityValid){
      // Find the article to modify
      const updatedArticles = articles_in_devis.map(article => {
        if (article.id === article_selected.id) {
          const updated = {
            ...article,
            quantite: Number(article_quantite),
            montant_HT: (article.prix_vente_HT * article_quantite).toFixed(2),
            montant_TVA: ((article.prix_vente_HT * article.taux_tva.taux) * article_quantite).toFixed(2),
            montant_TTC: ((article.prix_vente_HT * (1 + article.taux_tva.taux)) * article_quantite).toFixed(2),
          };
          return updated;
        }
        return article;
      });
      setArticlesInDevis(updatedArticles);
  
      // Recalculate total amounts
      const totalHT = updatedArticles.reduce((sum, a) => sum + parseFloat(a.montant_HT), 0).toFixed(2);
      const totalTVA = updatedArticles.reduce((sum, a) => sum + parseFloat(a.montant_TVA), 0).toFixed(2);
      const totalTTC = updatedArticles.reduce((sum, a) => sum + parseFloat(a.montant_TTC), 0).toFixed(2);
  
      setDevisMontantHT(totalHT);
      setDevisMontantTVA(totalTVA);
      setDevisMontantTTC(totalTTC);
  
      handleClose();
    }
  }

  const deleteArticle = () => {
  if (!article_selected || !article_selected.id) return;

  // Filter out the selected article
  const updatedArticles = articles_in_devis.filter(
    (article) => article.id !== article_selected.id
  );

  // Recalculate totals
  const totalHT = updatedArticles
    .reduce((sum, a) => sum + parseFloat(a.montant_HT), 0)
    .toFixed(2);
  const totalTVA = updatedArticles
    .reduce((sum, a) => sum + parseFloat(a.montant_TVA), 0)
    .toFixed(2);
  const totalTTC = updatedArticles
    .reduce((sum, a) => sum + parseFloat(a.montant_TTC), 0)
    .toFixed(2);

  // Update state
  setArticlesInDevis(updatedArticles);
  setDevisMontantHT(totalHT);
  setDevisMontantTVA(totalTVA);
  setDevisMontantTTC(totalTTC);

  // Close modal
  handleClose();
};


  // ### Add new article to devis ###
  
  const addNewArticle = async () => {
    const isQuantityValid = articleQuantityVerif(article_quantite);
    const isArticleSelected = article_selected.length !== 0;

    // If article is not already in the devis
    if (articles_in_devis.find(article => article.id === article_selected.id)) {
      alert("Cet article est déjà dans le devis.");
      return;
    }

    // Set article in devis if inputs are valid
    if (isQuantityValid && isArticleSelected) {
      const newArticle = {
        ...article_selected,
        quantite: article_quantite,
        montant_HT: (article_selected.prix_vente_HT * article_quantite).toFixed(2),
        montant_TVA: ((article_selected.prix_vente_HT * article_selected.taux_tva.taux) * article_quantite).toFixed(2),
        montant_TTC: ((article_selected.prix_vente_HT * (1 + article_selected.taux_tva.taux)) * article_quantite).toFixed(2),
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
    const isDateValid = devisDateVerif(devis_date);
    const isContentValid = devisContentVerif(articles_in_devis);

    const isformValid = isTitleValid && isDateValid && isContentValid;

    if (isformValid){
      const devisData = {
        title: devis_title,
        description: devis_description,
        date: devis_date,
        montant_HT: devis_montant_HT,
        montant_TVA: devis_montant_TVA,
        montant_TTC: devis_montant_TTC,
        statut: devis_status,
        client_id: id_client,
        articles: articles_in_devis.map(article => ({
          article_id: article.id,
          quantite: article.quantite,
        })),
      };

      if (isNewDevis) {
        // Create new devis
        httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/devis/create`, devisData)
        .then((resp) => {
          setIsNewDevis(false);
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
        .put(`${process.env.REACT_APP_BACKEND_URL}/devis/update/${id_devis}`, devisData)
        .then((resp) => {
          navigate(`/client/${id_client}`);
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

  // ### Delete devis
  const deleteDevis = async () => {
    httpClient
    .delete(`${process.env.REACT_APP_BACKEND_URL}/devis/delete/${id_devis}`)
      .then((resp) => {
        handleClose()
        navigate(`/client/${id_client}`);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  // ### Fetch devis, client info and every articles on page load ###
  const getDevisInfo = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/devis/info/${id_devis}`)
      .then((resp) => {
        setDevis(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.status === 404) {
            setIsNewDevis(true);
            setLoading(false);
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
      .get(`${process.env.REACT_APP_BACKEND_URL}/clients/info/${id_client}`)
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
  }

  const getAllArticles = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/articles/all`)
      .then((resp) => {
        setArticles(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.status !== 404) {
            alert(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  useEffect(() => {
    getClientInfo();
    getAllArticles();
    getDevisInfo();
  }, [isNewDevis]);

  // ### Filter articles logic ###
  useEffect(() => {
    if (articles && articles.data) {
      let currentArticles = articles.data;

      if (articleSearchTerm) {
        currentArticles = currentArticles.filter(art =>
          art.nom.toLowerCase().includes(articleSearchTerm.toLowerCase()) ||
          art.description.toLowerCase().includes(articleSearchTerm.toLowerCase())
        );
      }

      setFilteredArticles(currentArticles);
      setArticleCurrentPage(1);
    }
  }, [articles, articleSearchTerm]);

  // ### Pagination articles logic ###
  useEffect(() => {
    if (filteredArticles) {
      const startIndex = (articleCurrentPage - 1) * articleItemsPerPage;
      const endIndex = startIndex + articleItemsPerPage;
      setPaginatedArticles(filteredArticles.slice(startIndex, endIndex));
    }
  }, [filteredArticles, articleCurrentPage, articleItemsPerPage]);

  // Reset to page 1 when itemsPerPage changes
  useEffect(() => {
    setArticleCurrentPage(1);
  }, [articleItemsPerPage]);

  useEffect(() => {
  if (devis && !isNewDevis) {
    console.log("Update devis")
    setDevisTitle(devis.titre);
    setDevisDescription(devis.description);
    setDevisDate(devis.date);
    setDevisMontantHT(devis.montant_HT);
    setDevisMontantTVA(devis.montant_TVA);
    setDevisMontantTTC(devis.montant_TTC);
    setDevisStatus(devis.statut);

    if (Array.isArray(devis.articles)){
      setArticlesInDevis(
        devis.articles.map((da) => ({
          ...da.article,
          quantite: da.quantite,
          montant_HT: (da.article.prix_vente_HT * da.quantite).toFixed(2),
          montant_TVA: ((da.article.prix_vente_HT * da.article.taux_tva.taux) * da.quantite).toFixed(2),
          montant_TTC: ((da.article.prix_vente_HT * (1 + da.article.taux_tva.taux)) * da.quantite).toFixed(2),
        }))
      );
    }
    setLoading(false);
  }
}, [devis, isNewDevis]);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center">
        <h1 className="col-lg-11 col-10">Devis N°{id_devis}</h1>
        <button className="btn btn-danger col-lg-1 col-2" onClick={goBack}>Retour</button>
      </div>
      <br/>
      {client && (
        <>
          <h3>Client: {client.nom} {client.prenom}</h3>
          <h3>Adresse: {client.rue}, {client.code_postal} à {client.ville}</h3>
        </>
      )}
      <div className="row">
        <form className="col-lg-8 col-12">
          <div className="row">
            <div className="form-outline col-xl-4 col-6">
              <label className="form-label">Titre</label>
              <input type="text" id="titre" value={devis_title} onChange={(e) => {setDevisTitle(e.target.value);devisTitleVerif(e.target.value);}}
                className={`form-control form-control-lg ${devis_title_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un titre pour le devis"/>
              <div className="invalid-feedback">{devis_title_error}</div>
            </div>
            <div className="form-outline col-xl-3 col-6">
              <label className="form-label">Date</label>
              <input type="date" id="date" value={devis_date} onChange={(e) => {setDevisDate(e.target.value);devisDateVerif(e.target.value);}}
                className={`form-control form-control-lg ${devis_date_error ? "is-invalid" : form_submited ? "is-valid": ""}`}/>
              <div
              className="invalid-feedback">{devis_date_error}</div>
            </div>
          </div>
          <div className="row">
            <div className="form-outline col-xl-7 mt-4">
              <label className="form-label">Description</label>
              <textarea rows={3} id="description" value={devis_description} onChange={(e) => setDevisDescription(e.target.value)}
                className={`form-control form-control-lg`} placeholder="Entrer une description pour le devis"/>
            </div>
          </div>
          {!isNewDevis && devis && <h3 className="mt-4">{devis.statut === "Non signé" ? <p className="text-danger">{devis.statut}</p> : <p className="text-success">{devis.statut}</p>}</h3>}
        </form>
        <div className="col-lg-4 col-12 d-flex flex-column justify-content-end mt-lg-0 mt-4">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <span className="fw-bold">Montant total HT:</span>
            <span className="ms-2">{devis_montant_HT} €</span>
          </div>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <span className="fw-bold">Montant total TVA:</span>
            <span className="ms-2">{devis_montant_TVA} €</span>
          </div>
          <div className="d-flex justify-content-between align-items-center">
            <span className="fw-bold fs-5">Montant total TTC:</span>
            <span className="ms-2 fs-5 fw-bold">{devis_montant_TTC} €</span>
          </div>
        </div>
      </div>
      <table className="table table-hover table-striped mt-4">
        <thead>
          <tr>
            <th scope="col">Article</th>
            <th scope="col">Quantité</th>
            <th scope="col">Montant u. HT</th>
            <th scope="col">Montant u. TVA</th>
            <th scope="col">Montant u. TTC</th>
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          {articles_in_devis.length > 0 ? (
            articles_in_devis.map((article) => (
              <tr key={article.id}>
                <td onClick={() => handleModifyArticle(article)}>{article.nom}</td>
                <td onClick={() => handleModifyArticle(article)}>{article.quantite}</td>
                <td onClick={() => handleModifyArticle(article)}>{article.montant_HT} €</td>
                <td onClick={() => handleModifyArticle(article)}>{article.montant_TVA} €</td>
                <td onClick={() => handleModifyArticle(article)}>{article.montant_TTC} €</td>
                <td onClick={() => handleDeleteArticle(article)}><img src={trashCan} alt="trashcan"></img></td>
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
        <div>
          {!isNewDevis ? <button className="btn btn-danger me-4" onClick={handleDeleteDevis}> Supprimer le devis</button> : ""}
          {!isNewDevis ? <button className="btn btn-success me-4" onClick={() => navigate(`/devis/${id_client}/${id_devis}/pdf`)}>Générer le devis</button> : ""}
          <button className="btn btn-success" onClick={saveDevis}> Enregistrer le devis</button>
        </div>
      </div>
      <div className="modal fade" id="popup" tabIndex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
        <div className="modal-dialog modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h1 className="modal-title fs-5" id="popupLabel">{DELETE ? 'Supprimer le devis' : article_DELETE ? 'Supprimer l\'article du devis'  : article_MODIFY ? "Modifier la quantité de l'article" : "Ajouter un article"}</h1>
            </div>
            <div className="modal-body">
              {DELETE ? <h5>Êtes-vous sur de vouloir supprimer le devis {devis && devis.titre} {client && `de ${client.nom} ${client.prenom}`}?</h5> : 
              article_DELETE ? <h5>Êtes-vous sur de vouloir supprimer l'article {article_selected.nom} du devis ?</h5> :
              article_MODIFY ? (
                <div className="d-flex flex-inline align-items-center">
                  <p>Modifier le nombre de {article_selected.nom} :</p>
                  <div className="form-outline col-2 ms-4">
                    <input type="number" id="quantite" value={article_quantite} onChange={(e) => {setArticleQuantite(e.target.value);articleQuantityVerif(e.target.value);}}
                      className={`form-control form-control-lg ${article_quantity_error ? "is-invalid" : form_submited ? "is-valid": ""}`}/>
                    <div className="invalid-feedback">{article_quantity_error}</div>
                  </div>
                </div>
              ) : (
                <div>
                <div className="row mb-3 align-items-center">
                  <div className="col-md-9">
                    <input type="text" className="form-control form-control-lg" placeholder="Rechercher par nom, description..."
                      value={articleSearchTerm} onChange={(e) => setArticleSearchTerm(e.target.value)}/>
                  </div>
                  <div className="col-md-3">
                    <div className="d-flex align-items-center justify-content-end">
                      <label htmlFor="articleItemsPerPage" className="form-label me-2 mb-0">Articles:</label>
                      <select id="articleItemsPerPage" className="form-select form-select-lg w-auto" value={articleItemsPerPage}
                        onChange={(e) => setArticleItemsPerPage(Number(e.target.value))}>
                        <option value={5}>5</option>
                        <option value={10}>10</option>
                        <option value={25}>25</option>
                      </select>
                    </div>
                  </div>
                </div>
                <table className="table table-hover table-striped">
                  <thead>
                    <tr>
                      <th scope="col">Article</th>
                      <th scope="col">Description</th>
                      <th scope="col">Montant u. HT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedArticles.length > 0 ? (
                      paginatedArticles.map((article) => (
                        <tr key={article.id} className={article.id === article_selected.id ? 'table-active' : ''} onClick={() => {setArticleSelected(article);}}>
                          <td>{article.nom}</td>
                          <td>{article.description}</td>
                          <td>{article.prix_vente_HT} €</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3}>Aucun articles trouvé</td>
                      </tr>
                      )}
                  </tbody>
                </table>
                {filteredArticles.length > articleItemsPerPage && (
                  <nav>
                    <ul className="pagination justify-content-center">
                      <li className={`page-item ${articleCurrentPage === 1 ? 'disabled' : ''}`}>
                        <a className="page-link" href="!#" onClick={(e) => { e.preventDefault(); setArticleCurrentPage(articleCurrentPage - 1); }}>
                          Précédent
                        </a>
                      </li>
                      {Array.from({ length: Math.ceil(filteredArticles.length / articleItemsPerPage) }, (_, i) => i + 1).map(number => (
                        <li key={number} className={`page-item ${articleCurrentPage === number ? 'active' : ''}`}>
                          <a onClick={(e) => { e.preventDefault(); setArticleCurrentPage(number); }} href="!#" className='page-link'>
                            {number}
                          </a>
                        </li>
                      ))}
                      <li className={`page-item ${articleCurrentPage >= Math.ceil(filteredArticles.length / articleItemsPerPage) ? 'disabled' : ''}`}>
                        <a className="page-link" href="!#" onClick={(e) => { e.preventDefault(); setArticleCurrentPage(articleCurrentPage + 1); }}>
                          Suivant
                        </a>
                      </li>
                    </ul>
                  </nav>
                )}
                <form className="row mt-3">
                  <div className="col-5"/>
                  <div className="form-outline col-2">
                    <label className="form-label">Quantité</label>
                    <input type="number" id="quantite" value={article_quantite} onChange={(e) => {setArticleQuantite(e.target.value);articleQuantityVerif(e.target.value);}}
                      className={`form-control form-control-lg ${article_quantity_error ? "is-invalid" : form_submited ? "is-valid": ""}`}/>
                    <div className="invalid-feedback">{article_quantity_error}</div>
                  </div>
                  <div className="col-5"/>
                </form>
                </div>
              )}
            </div>
            <div className="modal-footer d-flex justify-content-center">
              {DELETE ? (
                <div>
                  <button className="btn btn-lg btn-danger me-4" onClick={handleClose}>Non</button>
                  <button className="btn btn-lg btn-primary" onClick={deleteDevis}>Oui</button>
                </div>
              ) : article_DELETE ? (
                <div>
                  <button className="btn btn-lg btn-danger me-4" onClick={handleClose}>Non</button>
                  <button className="btn btn-lg btn-primary" onClick={deleteArticle}>Oui</button>
                </div>
              ) : article_MODIFY ? (
                <div>
                  <button className="btn btn-lg btn-danger me-4" onClick={handleClose}>Annuler</button>
                  <button className="btn btn-lg btn-success" onClick={modifyArticle}>Modifier</button>
                </div>
              ) : [
                <div>
                  <button className="btn btn-lg btn-danger me-4" onClick={handleClose}>Annuler</button>
                  <button className="btn btn-lg btn-success" onClick={addNewArticle}>Ajouter</button>
                </div>
              ]}
              
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
export default Devis;