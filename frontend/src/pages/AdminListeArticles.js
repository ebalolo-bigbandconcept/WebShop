import { useEffect, useRef, useState } from "react";
import httpClient from "../components/httpClient";
import Modal from "../components/Modal";
import { useToast } from "../components/Toast";

function ListeArticles() {
  const [loading, setLoading] = useState(true);

  const [articles, setArticles] = useState([]);

  const [form_submited, setFormSubmited] = useState(false);
  const [article_nom, setArticleNom] = useState(null);
  const [article_description, setArticleDescription] = useState("");
  const [article_prix_achat_HT, setArticlePrixAchatHT] = useState(null);
  const [article_prix_vente_HT, setArticlePrixVenteHT] = useState(null);
  const [article_taux_tva, setArticleTauxTVA] = useState(0.20);
  const [vatRates, setVatRates] = useState([]);

  const [article_id, setArticleId] = useState("");
  const [article_nom_error, setArticleNomError] = useState("");
  const [article_description_error, setArticleDescriptionError] = useState("");
  const [article_prix_achat_HT_error, setArticlePrixAchatHTError] = useState("");
  const [article_prix_vente_HT_error, setArticlePrixVenteHTError] = useState("");

  const { showToast } = useToast();

  // Modal state
  const [MODIFY, setMODIFY] = useState(false);
  const [DELETE, setDELETE] = useState(false);
  const [CREATE, setCREATE] = useState(false);

  const modalRef = useRef(null);

  // Filter and Pagination state
  const [filteredArticles, setFilteredArticles] = useState([]);
  const [paginatedArticles, setPaginatedArticles] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  
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
    // Description is optional
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
    modalRef.current && modalRef.current.open();
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

    const isArticleNomValid = await articleNomVerif(article_nom);
    const isArticleDescriptionValid = await articleDescriptionVerif(article_description);
    const isArticlePrixAchatHTValid = await articlePrixAchatHTVerif(article_prix_achat_HT);

    const isFormValid = isArticleNomValid && isArticleDescriptionValid && isArticlePrixAchatHTValid;

    if (isFormValid) {
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/articles/create`, {
          nom: article_nom,
          description: article_description,
          prix_achat_HT: article_prix_achat_HT,
          taux_tva: article_taux_tva,
        })
        .then((resp) => {
          handleClose();
          showToast({ message: "Article ajouté", variant: "success" });
          getAllArticles();
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            if (error.response.status === 400) {
              showToast({ message: error.response.data.error, variant: "warning" });
            }
          } else {
            showToast({ message: "Une erreur est survenue.", variant: "danger" });
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
        showModal();
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          showToast({ message: error.response.data.error, variant: "danger" });
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
        }
      });
  }

  const modifyArticle = async () => {
    setFormSubmited(true);

    const isArticleNomValid = await articleNomVerif(article_nom);
    const isArticleDescriptionValid = await articleDescriptionVerif(article_description);
    const isArticlePrixAchatHTValid = await articlePrixAchatHTVerif(article_prix_achat_HT);
    const isFormValid = isArticleNomValid && isArticleDescriptionValid && isArticlePrixAchatHTValid;

    if (isFormValid) {
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/articles/update/${article_id}`, {
          nom: article_nom,
          description: article_description,
          prix_achat_HT: article_prix_achat_HT,
          taux_tva: article_taux_tva,
        })
        .then((resp) => {
          handleClose();
          showToast({ message: "Article mis à jour", variant: "success" });
          getAllArticles();
        })
        .catch((error) => {
          const errorMessage = error.response && error.response.data && error.response.data.error;
          if (errorMessage) {
            const variant = error.response.status === 400 ? "warning" : "danger";
            showToast({ message: errorMessage, variant });
          } else {
            showToast({ message: "Une erreur est survenue.", variant: "danger" });
          }
        });
    }
  }

  const handleDeleteArticle = async (article) => {
    setDELETE(true);
    setCREATE(false);
    setMODIFY(false);
    setArticleId(article.id);
    setArticleNom(article.nom);
    showModal();
  }

  const deleteArticle = async () => {
    httpClient
      .post(`${process.env.REACT_APP_BACKEND_URL}/articles/delete/${article_id}`)
      .then((resp) => {
        handleClose();
        showToast({ message: "Article supprimé", variant: "success" });
        getAllArticles();
      })
      .catch((error) => {
        const errorMessage = error.response && error.response.data && error.response.data.error;
        if (errorMessage) {
          const variant = error.response.status === 400 ? "warning" : "danger";
          showToast({ message: errorMessage, variant });
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
        }
      });
  }

  const getAllArticles = async () => {
    try {
        const resp = await httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/articles/all`);
        const items = Array.isArray(resp.data?.data) ? [...resp.data.data] : [];
        items.sort((a, b) => (a.id || 0) - (b.id || 0));
        setArticles(items);
        setFilteredArticles(items);
    } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
            if (error.response.data.error === "Aucuns articles trouvé") {
                setArticles([]);
                setFilteredArticles([]);
            } else {
            showToast({ message: "Une erreur est survenue lors du chargement des articles.", variant: "danger" });
            }
        } else {
          showToast({ message: "Une erreur est survenue lors du chargement des articles.", variant: "danger" });
        }
    } finally {
        setLoading(false);
    }
  }

  const handleClose = () => {
    modalRef.current && modalRef.current.close();
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
    // Load VAT rates for the select (public endpoint)
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/devis/tva`)
      .then((resp) => {
        const data = Array.isArray(resp.data?.data) ? resp.data.data : [];
        setVatRates(data);
        if (data.length > 0) {
          setArticleTauxTVA((prev) => (prev ?? data[0].taux));
        }
      })
      .catch((err) => {
        showToast({ message: "Erreur lors du chargement des taux de TVA", variant: "danger" });
      });
  }, []);

  // ### Filter Logic ###
  useEffect(() => {
    let currentArticles = articles;

    if (searchTerm) {
        currentArticles = currentArticles.filter(art => 
            art.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
            art.description.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }

    currentArticles = [...currentArticles].sort((a, b) => (a.id || 0) - (b.id || 0));
    setFilteredArticles(currentArticles);
    setCurrentPage(1);
  }, [articles, searchTerm]);

  // ### Pagination Logic ###
  useEffect(() => {
    if (filteredArticles) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      setPaginatedArticles(filteredArticles.slice(startIndex, endIndex));
    }
  }, [filteredArticles, currentPage, itemsPerPage]);

  // Reset to page 1 when itemsPerPage changes
  useEffect(() => {
    setCurrentPage(1);
  }, [itemsPerPage]);

  const modalTitle = CREATE
    ? "Ajouter un nouvel article."
    : MODIFY
      ? "Modifier l'article."
      : DELETE
        ? "Supprimer l'article."
        : "";

  const modalBody = DELETE ? (
    <h5>Êtes-vous sûr de vouloir supprimer l'article "{article_nom}" ?</h5>
  ) : (
    <form className="row">
      <div className="form-outline col-12">
        <label className="form-label">Article</label>
        <input
          type="text"
          id="article"
          value={article_nom}
          onChange={(e) => { setArticleNom(e.target.value); articleNomVerif(e.target.value); }}
          className={`form-control form-control-lg ${article_nom_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="Entrer un nom d'article"
        />
        <div className="invalid-feedback">{article_nom_error}</div>
      </div>
      <div className="form-outline col-12 mt-4">
        <label className="form-label">Description</label>
        <textarea
          id="prénom"
          value={article_description}
          onChange={(e) => { setArticleDescription(e.target.value); articleDescriptionVerif(e.target.value); }}
          className={`form-control form-control-lg ${article_description_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="Entrer une description"
        />
        <div className="invalid-feedback">{article_description_error}</div>
      </div>
      <div className="form-outline col-lg-5 col-4 mt-4">
        <label className="form-label">Prix d'achat HT</label>
        <input
          type="text"
          id="adresse"
          value={article_prix_achat_HT}
          onChange={(e) => {
            const value = e.target.value.replace(',', '.');
            setArticlePrixAchatHT(value);
            articlePrixAchatHTVerif(value);
          }}
          className={`form-control form-control-lg ${article_prix_achat_HT_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="10,00€"
        />
        <div className="invalid-feedback">{article_prix_achat_HT_error}</div>
      </div>
      {MODIFY && (
        <div className="form-outline col-lg-5 col-4 mt-4">
          <label className="form-label">Prix de vente HT (calculé)</label>
          <input type="text" id="prix_vente" value={article_prix_vente_HT} readOnly className="form-control form-control-lg" />
        </div>
      )}
      <div className={`form-outline ${MODIFY ? 'col-lg-2 col-4' : 'col-lg-7 col-8'} mt-4`}>
        <label className="form-label">TVA</label>
        <select
          id="taux_tva"
          value={article_taux_tva}
          onChange={(e) => setArticleTauxTVA(Number(e.target.value))}
          className="form-control form-control-lg"
        >
          {vatRates.length === 0 ? (
            <option value={0.20}>20%</option>
          ) : (
            vatRates.map((v) => (
              <option key={v.id} value={v.taux}>
                {(Number(v.taux) * 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, '')}%
              </option>
            ))
          )}
        </select>
      </div>
    </form>
  );

  const modalFooter = CREATE ? (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={handleClose}>Annuler</button>
      <button className="btn btn-lg btn-success" onClick={addNewArticle}>Ajouter</button>
    </div>
  ) : MODIFY ? (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={() => handleDeleteArticle({ id: article_id, nom: article_nom })}>Supprimer</button>
      <button className="btn btn-lg btn-success" onClick={modifyArticle}>Modifier</button>
    </div>
  ) : DELETE ? (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger me-4" onClick={handleClose}>Non</button>
      <button className="btn btn-lg btn-primary" onClick={deleteArticle}>Oui</button>
    </div>
  ) : null;

  if (loading) return <div>Chargement...</div>;
  
  return (
    <div>
      <h1>Liste des articles</h1>
      <br/>
      <Modal ref={modalRef} title={modalTitle} footer={modalFooter} size="modal-lg">
        {modalBody}
      </Modal>

      <div className="row mb-3 align-items-center">
        <div className="col-md-9">
          <input type="text" className="form-control form-control-lg" placeholder="Rechercher par nom, description..."
            value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}/>
        </div>
        <div className="col-md-3">
            <div className="d-flex align-items-center justify-content-end">
                <label htmlFor="itemsPerPage" className="form-label me-2 mb-0">Articles par page:</label>
                <select id="itemsPerPage" className="form-select form-select-lg w-auto" value={itemsPerPage}
                    onChange={(e) => setItemsPerPage(Number(e.target.value))}>
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                </select>
            </div>
        </div>
      </div>
      <div className="d-flex justify-content-end w-100">
        <button className="btn btn-lg btn-success mt-4" onClick={handleCreateArticle}>+ Ajouter un nouvel article</button>
      </div>
      <table className="table table-hover table-striped mt-4">
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
          {paginatedArticles.length > 0 ? (
            paginatedArticles.map((article) => (
              <tr key={article.id} onClick={() => {handleModifyArticle(article.id)}}>
                <td>{article.id}</td>
                <td>{article.nom}</td>
                <td>{article.description}</td>
                <td>{article.prix_achat_HT} €</td>
                <td>{article.prix_vente_HT} €</td>
                <td>{((Number(article.taux_tva.taux) * 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, ''))} %</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={6}>Aucun articles trouvé</td>
            </tr>
          )}
        </tbody>
      </table>

      {filteredArticles.length > itemsPerPage && (
        <nav>
          <ul className="pagination justify-content-center">
            <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
              <a className="page-link" href="!#" onClick={(e) => { e.preventDefault(); setCurrentPage(currentPage - 1); }}>
                Précédent
              </a>
            </li>
            {Array.from({ length: Math.ceil(filteredArticles.length / itemsPerPage) }, (_, i) => i + 1).map(number => (
              <li key={number} className={`page-item ${currentPage === number ? 'active' : ''}`}>
                <a onClick={(e) => { e.preventDefault(); setCurrentPage(number); }} href="!#" className='page-link'>
                  {number}
                </a>
              </li>
            ))}
            <li className={`page-item ${currentPage >= Math.ceil(filteredArticles.length / itemsPerPage) ? 'disabled' : ''}`}>
              <a className="page-link" href="!#" onClick={(e) => { e.preventDefault(); setCurrentPage(currentPage + 1); }}>
                Suivant
              </a>
            </li>
          </ul>
        </nav>
      )}
    </div>
  );
}
export default ListeArticles;