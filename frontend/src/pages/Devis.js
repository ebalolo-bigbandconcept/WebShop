import { useParams } from "react-router";
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import httpClient from "../components/httpClient";
import Modal from "../components/Modal";
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
  const [selectedArticleIds, setSelectedArticleIds] = useState([]);
  const [selectAllLines, setSelectAllLines] = useState(false);

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
  const [include_location, setIncludeLocation] = useState(false);
  const [first_contribution_amount, setFirstContributionAmount] = useState(0);
  const [location_subscription_cost, setLocationSubscriptionCost] = useState(0);
  const [location_interests_cost, setLocationInterestsCost] = useState(0);
  const [location_time, setLocationTime] = useState(0); // in months
  const [location_monthly_total, setLocationMonthlyTotal] = useState(0);
  const [location_monthly_total_ht, setLocationMonthlyTotalHt] = useState(0);
  const [devis_location_total, setDevisLocationTotal] = useState(0);
  const [devis_location_total_ht, setDevisLocationTotalHt] = useState(0);

  const [devis_title_error, setDevisTitleError] = useState("");
  const [devis_date_error, setDevisDateError] = useState("");

  const [article_quantity_error, setArticleQuantityError] = useState("");

  const [isNewDevis, setIsNewDevis] = useState(false);

  const [DELETE, setDELETE] = useState(false);
  const [article_MODIFY, setArticleMODIFY] = useState(false);
  const [article_DELETE, setArticleDELETE] = useState(false);

  const modalRef = useRef(null);
  const goBack = () => {
    navigate(-1);
  };

  const articleQuantityVerif = (value) => {
    const qty = Number(value);
    if (!value || isNaN(qty) || qty <= 0 || !Number.isFinite(qty)) {
      setArticleQuantityError("Veuillez entrer une quantité valide (> 0)");
      return false;
    }
    setArticleQuantityError("");
    return true;
  };

  const devisTitleVerif = (value) => {
    if (!value || String(value).trim() === "") {
      setDevisTitleError("Veuillez entrer un titre");
      return false;
    }
    setDevisTitleError("");
    return true;
  };

  const devisDateVerif = (value) => {
    if (!value) {
      setDevisDateError("Veuillez entrer une date");
      return false;
    }
    const d = new Date(value);
    if (isNaN(d.getTime())) {
      setDevisDateError("Format de date invalide");
      return false;
    }
    setDevisDateError("");
    return true;
  };

  const devisContentVerif = (articles) => {
    const isValid = Array.isArray(articles) && articles.length > 0;
    if (!isValid) {
      alert("Veuillez ajouter au moins un article au devis.");
    }
    return isValid;
  };

  const toggleSelectAllLines = () => {
    if (selectAllLines) {
      setSelectAllLines(false);
      setSelectedArticleIds([]);
      return;
    }
    const allIds = articles_in_devis.map((a) => a.id);
    setSelectedArticleIds(allIds);
    setSelectAllLines(true);
  };

  const toggleSelectLine = (id) => {
    setSelectedArticleIds((prev) => {
      const exists = prev.includes(id);
      const next = exists ? prev.filter((x) => x !== id) : [...prev, id];
      setSelectAllLines(next.length === articles_in_devis.length && articles_in_devis.length > 0);
      return next;
    });
  };
  const showModal = () => {
    modalRef.current && modalRef.current.open();
  };
  const applyVatToSelected = (taux) => {
    if (selectedArticleIds.length === 0) return;
    const updated = articles_in_devis.map((article) => {
      if (!selectedArticleIds.includes(article.id)) return article;
      const taux_tva = { ...(article.taux_tva || {}), taux };
      const montant_HT = (article.prix_vente_HT * article.quantite).toFixed(2);
      const montant_TVA = ((article.prix_vente_HT * taux) * article.quantite).toFixed(2);
      const montant_TTC = ((article.prix_vente_HT * (1 + taux)) * article.quantite).toFixed(2);
      return { ...article, taux_tva, montant_HT, montant_TVA, montant_TTC };
    });
    setArticlesInDevis(updated);

    const totalHT = updated.reduce((sum, a) => sum + parseFloat(a.montant_HT), 0).toFixed(2);
    const totalTVA = updated.reduce((sum, a) => sum + parseFloat(a.montant_TVA), 0).toFixed(2);
    const totalTTC = updated.reduce((sum, a) => sum + parseFloat(a.montant_TTC), 0).toFixed(2);
    setDevisMontantHT(totalHT);
    setDevisMontantTVA(totalTVA);
    setDevisMontantTTC(totalTTC);

    // Clear selection after applying VAT
    setSelectedArticleIds([]);
    setSelectAllLines(false);
  };

  const handleClose = () => {
    modalRef.current && modalRef.current.close();

    setArticleQuantite(1);
    setArticleSelected([]);
    setArticleQuantityError("");
    setArticleSearchTerm("");
    setArticleCurrentPage(1);
    setDELETE(false);
    setArticleMODIFY(false);
    setArticleDELETE(false);
  }

  const handleAddArticle = () => {
    setDELETE(false);
    setArticleDELETE(false);
    setArticleMODIFY(false);
    setFormSubmited(false);
    setArticleQuantityError("");
    setArticleQuantite(1);
    showModal();
  };

  const handleModifyArticle = (article) => {
    setDELETE(false);
    setArticleDELETE(false);
    setArticleMODIFY(true);
    setArticleSelected(article);
    setArticleQuantite(article.quantite);
    setArticleQuantityError("");
    showModal();
  };

  const handleDeleteArticle = (article) => {
    setDELETE(false);
    setArticleDELETE(true);
    setArticleMODIFY(false);
    setArticleSelected(article);
    showModal();
  };

  const handleDeleteDevis = () => {
    setDELETE(true);
    setArticleDELETE(false);
    setArticleMODIFY(false);
    showModal();
  };

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
        taux_tva: article_selected.taux_tva,
        montant_HT: (article_selected.prix_vente_HT * article_quantite).toFixed(2),
        montant_TVA: ((article_selected.prix_vente_HT * (article_selected.taux_tva?.taux ?? 0.20)) * article_quantite).toFixed(2),
        montant_TTC: ((article_selected.prix_vente_HT * (1 + (article_selected.taux_tva?.taux ?? 0.20))) * article_quantite).toFixed(2),
        commentaire: '',
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
        is_location: include_location,
        first_contribution_amount: include_location ? first_contribution_amount : null,
        location_monthly_total: include_location ? location_monthly_total : null,
        location_monthly_total_ht: include_location ? location_monthly_total_ht : null,
        location_total: include_location ? devis_location_total : null,
        location_total_ht: include_location ? devis_location_total_ht : null,
        articles: articles_in_devis.map(article => ({
          article_id: article.id,
          quantite: article.quantite,
          taux_tva: article.taux_tva?.taux,
          commentaire: article.commentaire || null,
        })),
      };

      if (isNewDevis) {
        // Create new devis
        httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/devis/create`, devisData)
        .then(async (resp) => {
          const newDevisId = resp.data && resp.data.id;
          if (!newDevisId) {
            alert('Erreur: id du devis manquant après création.');
            return;
          }
          
          // Set isNewDevis to false first to prevent the useEffect from fetching too early
          setIsNewDevis(false);
          
          // Fetch the newly created devis with retry logic
          let retries = 3;
          let fetchSuccess = false;
          
          while (retries > 0 && !fetchSuccess) {
            try {
              await new Promise(resolve => setTimeout(resolve, 300)); // Wait 300ms
              const data = await fetchDevisById(newDevisId);
              if (data) {
                fetchSuccess = true;
                // Update URL to reflect the new devis ID only after successful fetch
                navigate(`/devis/${id_client}/${newDevisId}`, { replace: true });
              }
            } catch (error) {
              retries--;
              if (retries === 0) {
                alert("Le devis a été créé mais il y a eu un problème lors du rechargement. Veuillez rafraîchir la page.");
                navigate(`/devis/${id_client}/${newDevisId}`, { replace: true });
              }
            }
          }
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
    const targetId = (devis && devis.id) ? devis.id : id_devis;
    if (!targetId) {
      alert('Impossible de supprimer: aucun id de devis valide.');
      return;
    }

    httpClient
    .delete(`${process.env.REACT_APP_BACKEND_URL}/devis/delete/${targetId}`)
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
    // kept for backwards compatibility, delegates to fetchDevisById
    return fetchDevisById(id_devis);
  }

  const fetchDevisById = async (targetId) => {
    setLoading(true);
    if (!targetId) {
      setIsNewDevis(true);
      setLoading(false);
      return null;
    }

    try {
      const resp = await httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/devis/info/${targetId}`);
      const data = resp.data;
      setDevis(data);
      setIsNewDevis(false);

      // initialize form fields from fetched devis
      setDevisTitle(data.titre);
      setDevisDescription(data.description);
      setDevisDate(data.date);
      setDevisMontantHT(data.montant_HT);
      setDevisMontantTVA(data.montant_TVA);
      setDevisMontantTTC(data.montant_TTC);
      setDevisStatus(data.statut);
      setIncludeLocation(data.is_location || false);
      setFirstContributionAmount(data.first_contribution_amount || 0);
      setLocationMonthlyTotal(data.location_monthly_total || 0);
      setDevisLocationTotal(data.location_total || 0);

      if (Array.isArray(data.articles)) {
        setArticlesInDevis(
          data.articles.map((da) => {
            const taux = (da.taux_tva && da.taux_tva.taux != null) ? da.taux_tva.taux : da.article.taux_tva.taux;
            return {
              ...da.article,
              quantite: da.quantite,
              taux_tva: { taux },
              montant_HT: (da.article.prix_vente_HT * da.quantite).toFixed(2),
              montant_TVA: ((da.article.prix_vente_HT * taux) * da.quantite).toFixed(2),
              montant_TTC: ((da.article.prix_vente_HT * (1 + taux)) * da.quantite).toFixed(2),
              commentaire: da.commentaire || '',
            };
          })
        );
      } else {
        setArticlesInDevis([]);
      }

      setLoading(false);
      return data;
    } catch (error) {
      if (error.response && error.response.status === 404) {
        setIsNewDevis(true);
        setLoading(false);
        throw error; // Re-throw to allow retry logic in saveDevis
      }
      console.error(error);
      setLoading(false);
      throw error; // Re-throw to allow retry logic
    }
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

  const getParameters = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/admin/parameters`)
      .then((resp) => {
        setLocationSubscriptionCost(resp.data.locationSubscriptionCost || 0);
        setLocationInterestsCost(resp.data.locationInterestsCost || resp.data.locationMaintenanceCost || 0);
        setLocationTime(resp.data.locationTime || 0); // in months
      })
      .catch((error) => {
        console.error("Error fetching parameters:", error);
      });
  }

  const recomputeLocationTotals = (apportValue = first_contribution_amount, includeFlag = include_location) => {
    if (!includeFlag) {
      setLocationMonthlyTotal(0);
      setLocationMonthlyTotalHt(0);
      setDevisLocationTotal(0);
      setDevisLocationTotalHt(0);
      return;
    }

    const articlesTTC = parseFloat(devis_montant_TTC) || 0;
    const subscriptionTTC = parseFloat(location_subscription_cost) || 0;
    const interestsTTC = parseFloat(location_interests_cost) || 0;
    const apport = parseFloat(apportValue) || 0;

    const totalHTValue = articlesTTC + subscriptionTTC + interestsTTC - apport;
    const totalHT = totalHTValue.toFixed(2);

    const totalTTCValue = totalHTValue * 1.20;
    const totalTTC = totalTTCValue.toFixed(2);

    const monthlyHT = location_time > 0 ? (totalHTValue / location_time).toFixed(2) : 0;
    const monthlyTTC = location_time > 0 ? (totalTTCValue / location_time).toFixed(2) : 0;

    setDevisLocationTotalHt(totalHT);
    setDevisLocationTotal(totalTTC);
    setLocationMonthlyTotalHt(monthlyHT);
    setLocationMonthlyTotal(monthlyTTC);
  };

  const handleLocationToggle = (checked) => {
    setIncludeLocation(checked);
    recomputeLocationTotals(first_contribution_amount, checked);
  }

  const handleApportChange = (value) => {
    const apport = parseFloat(value) || 0;
    setFirstContributionAmount(apport);

    if (include_location) {
      recomputeLocationTotals(apport, true);
    }
  }

  useEffect(() => {
    getClientInfo();
    getAllArticles();
    getParameters();
    // fetch current devis on id change, but not if we're in the middle of creating a new one
    if (!isNewDevis || id_devis) {
      fetchDevisById(id_devis);
    }
  }, [id_devis]);

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
    setIncludeLocation(devis.is_location || false);
    setFirstContributionAmount(devis.first_contribution_amount || 0);
    setLocationMonthlyTotal(devis.location_monthly_total || 0);
    setDevisLocationTotal(devis.location_total || 0);

    if (Array.isArray(devis.articles)){
      setArticlesInDevis(
        devis.articles.map((da) => {
          const taux = (da.taux_tva && da.taux_tva.taux != null) ? da.taux_tva.taux : da.article.taux_tva.taux;
          return {
            ...da.article,
            quantite: da.quantite,
            taux_tva: { taux },
            montant_HT: (da.article.prix_vente_HT * da.quantite).toFixed(2),
            montant_TVA: ((da.article.prix_vente_HT * taux) * da.quantite).toFixed(2),
            montant_TTC: ((da.article.prix_vente_HT * (1 + taux)) * da.quantite).toFixed(2),
            commentaire: da.commentaire || '',
          };
        })
      );
    }
    setLoading(false);
  }
}, [devis, isNewDevis]);

  useEffect(() => {
    if (!loading) {
      recomputeLocationTotals();
    }
  }, [include_location, devis_montant_HT, devis_montant_TTC, location_subscription_cost, location_interests_cost, location_time, first_contribution_amount, loading]);

  useEffect(() => {
    if (include_location && !loading) {
      const locationTab = document.getElementById('location-tab');
      if (locationTab) {
        locationTab.click();
      }
    }
  }, [include_location, loading]);

  const modalTitle = DELETE
    ? 'Supprimer le devis'
    : article_DELETE
      ? "Supprimer l'article du devis"
      : article_MODIFY
        ? "Modifier la quantité de l'article"
        : "Ajouter un article";

  const modalBody = DELETE ? (
    <h5>
      Êtes-vous sur de vouloir supprimer le devis {devis && devis.titre} {client && `de ${client.nom} ${client.prenom}`}?
    </h5>
  ) : article_DELETE ? (
    <h5>Êtes-vous sur de vouloir supprimer l'article {article_selected?.nom} du devis ?</h5>
  ) : article_MODIFY ? (
    <div className="d-flex flex-inline align-items-center">
      <p>Modifier le nombre de {article_selected?.nom} :</p>
      <div className="form-outline col-2 ms-4">
        <input
          type="number"
          id="quantite"
          value={article_quantite}
          onChange={(e) => { setArticleQuantite(e.target.value); articleQuantityVerif(e.target.value); }}
          className={`form-control form-control-lg ${article_quantity_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
        />
        <div className="invalid-feedback">{article_quantity_error}</div>
      </div>
    </div>
  ) : (
    <div>
      <div className="row mb-3 align-items-center">
        <div className="col-md-9">
          <input
            type="text"
            className="form-control form-control-lg"
            placeholder="Rechercher par nom, description..."
            value={articleSearchTerm}
            onChange={(e) => setArticleSearchTerm(e.target.value)}
          />
        </div>
        <div className="col-md-3">
          <div className="d-flex align-items-center justify-content-end">
            <label htmlFor="articleItemsPerPage" className="form-label me-2 mb-0">Articles:</label>
            <select
              id="articleItemsPerPage"
              className="form-select form-select-lg w-auto"
              value={articleItemsPerPage}
              onChange={(e) => setArticleItemsPerPage(Number(e.target.value))}
            >
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
              <tr
                key={article.id}
                className={article.id === article_selected?.id ? 'table-active' : ''}
                onClick={() => { setArticleSelected(article); }}
              >
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
          <input
            type="number"
            id="quantite"
            value={article_quantite}
            onChange={(e) => { setArticleQuantite(e.target.value); articleQuantityVerif(e.target.value); }}
            className={`form-control form-control-lg ${article_quantity_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          />
          <div className="invalid-feedback">{article_quantity_error}</div>
        </div>
        <div className="col-5"/>
      </form>
    </div>
  );

  const modalFooter = DELETE ? (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={handleClose}>Non</button>
      <button className="btn btn-lg btn-primary" onClick={deleteDevis}>Oui</button>
    </div>
  ) : article_DELETE ? (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={handleClose}>Annuler</button>
      <button className="btn btn-lg btn-success" onClick={deleteArticle}>Supprimer</button>
    </div>
  ) : article_MODIFY ? (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={handleClose}>Annuler</button>
      <button className="btn btn-lg btn-success" onClick={modifyArticle}>Modifier</button>
    </div>
  ) : (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={handleClose}>Annuler</button>
      <button className="btn btn-lg btn-success" onClick={addNewArticle}>Ajouter</button>
    </div>
  );

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
          {id_devis && (
            <div className="mt-4 d-flex flex-wrap align-items-center gap-3">
              <h3 className={`m-0 ${devis_status === "Non signé" || devis_status === "En attente de signature" ? "text-danger" : devis_status === "Signé" ? "text-success" : "text-warning"}`}>{devis_status}</h3>
              {(devis_status === "Non signé" || devis_status === "En attente de signature") && (
                <div className="form-check mb-0 d-flex align-items-center gap-2">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="marquerSigne"
                    checked={devis_status === "Signé"}
                    onChange={(e) => {
                      if (e.target.checked && window.confirm("Voulez-vous marquer ce devis comme signé ?")) {
                        setDevisStatus("Signé");
                      } else {
                        e.target.checked = false;
                      }
                    }}
                  />
                  <label className="form-check-label mb-0" htmlFor="marquerSigne">
                    Marquer comme signé
                  </label>
                </div>
              )}
            </div>
          )}
        </form>
        <div className="col-lg-4 col-12 d-flex flex-column justify-content-end mt-lg-0 mt-4">
          <ul className="nav nav-tabs mb-3" role="tablist">
            <li className="nav-item" role="presentation">
              <button className="nav-link active" id="articles-tab" data-bs-toggle="tab" data-bs-target="#articles-pane" type="button" role="tab" aria-controls="articles-pane" aria-selected="true">
                Articles
              </button>
            </li>
            {include_location && (
              <li className="nav-item" role="presentation">
                <button className="nav-link" id="location-tab" data-bs-toggle="tab" data-bs-target="#location-pane" type="button" role="tab" aria-controls="location-pane" aria-selected="false">
                  Location
                </button>
              </li>
            )}
          </ul>

          <div className="tab-content" id="totalsTabContent">
            <div className="tab-pane fade show active" id="articles-pane" role="tabpanel" aria-labelledby="articles-tab">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="fw-bold">Montant total HT:</span>
                <span className="ms-2">{devis_montant_HT} €</span>
              </div>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="fw-bold">Montant total TVA:</span>
                <span className="ms-2">{devis_montant_TVA} €</span>
              </div>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <span className="fw-bold fs-5">Montant total TTC:</span>
                <span className="ms-2 fs-5 fw-bold">{devis_montant_TTC} €</span>
              </div>
              <hr />
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="includeLocation"
                  checked={include_location}
                  onChange={(e) => handleLocationToggle(e.target.checked)}
                />
                <label className="form-check-label" htmlFor="includeLocation">
                  Location
                </label>
              </div>
            </div>

            {include_location && (
              <div className="tab-pane fade" id="location-pane" role="tabpanel" aria-labelledby="location-tab">
                <div className="mb-3">
                  <small className="text-muted">
                    Durée location: {Math.floor(location_time / 12)} an{Math.floor(location_time / 12) !== 1 ? 's' : ''}{location_time % 12 > 0 ? ` ${location_time % 12} mois` : ''}
                  </small>
                </div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="fw-bold">Articles TTC:</span>
                  <span className="ms-2">{devis_montant_TTC} €</span>
                </div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="fw-bold">Abonement:</span>
                  <span className="ms-2">{location_subscription_cost} €</span>
                </div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="fw-bold">Intérêts:</span>
                  <span className="ms-2">{location_interests_cost} €</span>
                </div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span className="fw-bold">Apport:</span>
                  <div className="d-flex align-items-center">
                    <input type="number" className="form-control form-control-sm" style={{width: '100px'}} value={first_contribution_amount} onChange={(e) => handleApportChange(e.target.value)} step="0.01" min="0" />
                    <span className="ms-2">€</span>
                  </div>
                </div>
                <div className="d-flex justify-content-between align-items-center mb-2 border-top pt-2">
                  <span className="fw-bold">Mensuel HT:</span>
                  <span className="ms-2 fw-bold">{location_monthly_total_ht} €</span>
                </div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="fw-bold">Mensuel TTC:</span>
                  <span className="ms-2 fw-bold">{location_monthly_total} €</span>
                </div>
                <div className="d-flex justify-content-between align-items-center border-top pt-2">
                  <span className="fw-bold fs-6">Total Location HT:</span>
                  <span className="ms-2 fw-bold">{devis_location_total_ht} €</span>
                </div>
                <div className="d-flex justify-content-between align-items-center">
                  <span className="fw-bold fs-5">Total Location TTC:</span>
                  <span className="ms-2 fs-5 fw-bold">{devis_location_total} €</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="d-flex align-items-center mb-3 mt-4">
        <span className="me-3">TVA sélectionnée:</span>
        <button className="btn btn-outline-secondary me-2" onClick={() => applyVatToSelected(0.20)}>20%</button>
        <button className="btn btn-outline-secondary" onClick={() => applyVatToSelected(0.10)}>10%</button>
      </div>
      <table className="table table-hover table-striped mt-4">
        <thead>
          <tr>
            <th scope="col"><input type="checkbox" checked={selectAllLines} onChange={toggleSelectAllLines} /></th>
            <th scope="col">Article</th>
            <th scope="col">Quantité</th>
            <th scope="col">TVA</th>
            <th scope="col">Montant u. HT</th>
            <th scope="col">Montant u. TVA</th>
            <th scope="col">Montant u. TTC</th>
            <th scope="col">Commentaire</th>
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          {articles_in_devis.length > 0 ? (
            articles_in_devis.map((article) => (
              <tr key={article.id}>
                <td><input type="checkbox" checked={selectedArticleIds.includes(article.id)} onChange={() => toggleSelectLine(article.id)} /></td>
                <td onClick={() => handleModifyArticle(article)}>{article.nom}{(article.taux_tva?.taux ?? 0) === 0.10 ? ' (Rénovation)' : ''}</td>
                <td onClick={() => handleModifyArticle(article)}>{article.quantite}</td>
                <td onClick={() => handleModifyArticle(article)}>{((article.taux_tva?.taux ?? 0) * 100).toFixed(0)} %</td>
                <td onClick={() => handleModifyArticle(article)}>{article.montant_HT} €</td>
                <td onClick={() => handleModifyArticle(article)}>{article.montant_TVA} €</td>
                <td onClick={() => handleModifyArticle(article)}>{article.montant_TTC} €</td>
                <td>
                  <input
                    type="text"
                    className="form-control form-control-sm"
                    value={article.commentaire || ''}
                    onChange={(e) => {
                      const value = e.target.value;
                      setArticlesInDevis(prev => prev.map(a => a.id === article.id ? { ...a, commentaire: value } : a));
                    }}
                    placeholder="Commentaire"
                  />
                </td>
                <td onClick={() => handleDeleteArticle(article)}><img src={trashCan} alt="trashcan"></img></td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={9}>Aucun articles</td>
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
      <Modal ref={modalRef} title={modalTitle} footer={modalFooter} size="modal-lg" backdrop="static" keyboard={false}>
        {modalBody}
      </Modal>
    </div>
  );
}
export default Devis;