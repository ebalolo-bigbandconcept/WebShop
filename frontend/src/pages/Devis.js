import { PlusLg, Trash3Fill, ArrowReturnLeft, FloppyFill, FileEarmarkPdf } from "react-bootstrap-icons";
import { useParams } from "react-router";
import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import Quill from "quill";
import "quill/dist/quill.snow.css";
import httpClient from "../components/httpClient";
import Modal from "../components/Modal";
import { useToast } from "../components/Toast";

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
  const [vatRates, setVatRates] = useState([]);

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
  const [devis_remise, setDevisRemise] = useState(0);
  const [devis_status, setDevisStatus] = useState("Non signé");
  const [selected_scenario, setSelectedScenario] = useState(null); // tracks which scenario client selected
  const [first_contribution_amount, setFirstContributionAmount] = useState(0);
  const [location_subscription_cost, setLocationSubscriptionCost] = useState(0);
  const [location_interests_cost, setLocationInterestsCost] = useState(0);
  const [location_time, setLocationTime] = useState(0); // in months

  const [devis_title_error, setDevisTitleError] = useState("");
  const [devis_date_error, setDevisDateError] = useState("");

  const [article_quantity_error, setArticleQuantityError] = useState("");

  const [isNewDevis, setIsNewDevis] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [DELETE, setDELETE] = useState(false);
  const [article_MODIFY, setArticleMODIFY] = useState(false);
  const [article_DELETE, setArticleDELETE] = useState(false);

  const { showToast } = useToast();

  const modalRef = useRef(null);
  const commentModalRef = useRef(null);
  const commentEditorRef = useRef(null);
  const commentQuillRef = useRef(null);
  const commentInitialContentLoaded = useRef(false);
  const [commentEditingArticleId, setCommentEditingArticleId] = useState(null);
  const [commentDraft, setCommentDraft] = useState("");
  const isLocked = !isNewDevis && devis?.statut === "Signé";
  const isPendingOrSigned = devis_status === "En attente de signature" || devis_status === "Signé";
  const isLocationDisabled = isPendingOrSigned && selected_scenario === "direct";
  const isApportDisabled = isPendingOrSigned && selected_scenario === "location_without_apport";

  const blockSignedEdit = () => {
    if (isLocked) {
      showToast({ message: "Devis signé : modification interdite.", variant: "warning" });
      return true;
    }
    return false;
  };
  const goBack = () => {
    const state = location.state;
    if (state && state.from) {
      navigate(state.from, { replace: true });
    } else {
      navigate(-1);
    }
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
      showToast({ message: "Veuillez ajouter au moins un article au devis.", variant: "warning" });
    }
    return isValid;
  };

  const toggleSelectAllLines = () => {
    if (isLocked) return;
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
    if (isLocked) return;
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
    if (blockSignedEdit()) return;
    if (selectedArticleIds.length === 0) return;
    // Update article VAT rates and recalculate amounts for immediate display
    const updated = articles_in_devis.map((article) => {
      if (!selectedArticleIds.includes(article.id)) return article;
      const taux_tva = { ...(article.taux_tva || {}), taux };
      const unit_price = parseFloat(article.prix_vente_HT) || 0;
      const qty = parseFloat(article.quantite) || 0;
      const vat = parseFloat(taux) || 0;
      const montant_HT = (unit_price * qty).toFixed(2);
      const montant_TVA = (unit_price * vat * qty).toFixed(2);
      const montant_TTC = (unit_price * (1 + vat) * qty).toFixed(2);
      return {
        ...article,
        taux_tva,
        montant_HT,
        montant_TVA,
        montant_TTC,
      };
    });
    setArticlesInDevis(updated);
    // Backend will recalculate amounts when devis is saved
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
    
    // Clean up comment editor
    setCommentEditingArticleId(null);
    setCommentDraft("");
    if (commentQuillRef.current) {
      commentQuillRef.current = null;
    }
    if (commentEditorRef.current) {
      commentEditorRef.current.innerHTML = '';
    }
    commentInitialContentLoaded.current = false;
  }

  const stripHtml = (value) => {
    if (!value) return "";
    return value
      .replace(/<[^>]*>/g, " ")
      .replace(/&nbsp;/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  };

  useEffect(() => {
    if (!commentEditingArticleId) return;
    if (!commentEditorRef.current) return;
    if (commentQuillRef.current) return; // Already initialized
    
    // Clean the container and its parent from any Quill artifacts
    const container = commentEditorRef.current;
    const parent = container.parentElement;
    
    // Remove any existing toolbar in the parent
    const existingToolbar = parent?.querySelector('.ql-toolbar');
    if (existingToolbar) {
      existingToolbar.remove();
    }
    
    // Clear the editor container
    container.innerHTML = '';
    
    const quill = new Quill(container, {
      theme: "snow",
      modules: {
        toolbar: [
          [{ header: [1, 2, 3, false] }],
          ["bold", "italic", "underline", "strike"],
          [{ list: "ordered" }, { list: "bullet" }, { indent: "-1" }, { indent: "+1" }],
          ["link"],
          ["clean"],
        ],
      },
    });
    
    quill.on("text-change", () => {
      setCommentDraft(quill.root.innerHTML);
    });
    
    commentQuillRef.current = quill;
    
    // Set initial content
    if (commentDraft) {
      quill.root.innerHTML = commentDraft;
      commentInitialContentLoaded.current = true;
    } else {
      commentInitialContentLoaded.current = true;
    }
  }, [commentEditingArticleId, article_MODIFY]);

  // ### Load content when commentDraft changes ###
  useEffect(() => {
    if (!commentQuillRef.current) return;
    if (commentInitialContentLoaded.current) return;
    
    if (commentDraft) {
      commentQuillRef.current.root.innerHTML = commentDraft;
      commentInitialContentLoaded.current = true;
    }
  }, [commentDraft]);

  const openCommentEditor = (article) => {
    if (blockSignedEdit()) return;
    setCommentEditingArticleId(article.id);
    setCommentDraft(article.commentaire || "");
    commentModalRef.current && commentModalRef.current.open();
  };

  const closeCommentEditor = () => {
    commentModalRef.current && commentModalRef.current.close();
    setCommentEditingArticleId(null);
    setCommentDraft("");
    
    // Clean up Quill editor
    if (commentQuillRef.current) {
      commentQuillRef.current = null;
    }
    if (commentEditorRef.current) {
      commentEditorRef.current.innerHTML = '';
    }
    
    // Reset initial content flag
    commentInitialContentLoaded.current = false;
  };

  const saveCommentEditor = () => {
    if (commentEditingArticleId == null) return;
    setArticlesInDevis((prev) =>
      prev.map((a) =>
        a.id === commentEditingArticleId ? { ...a, commentaire: commentDraft } : a
      )
    );
    closeCommentEditor();
  };

  const handleAddArticle = () => {
    if (blockSignedEdit()) return;
    setDELETE(false);
    setArticleDELETE(false);
    setArticleMODIFY(false);
    setFormSubmited(false);
    setArticleQuantityError("");
    setArticleQuantite(1);
    showModal();
  };

  const handleModifyArticle = (article) => {
    if (blockSignedEdit()) return;
    setDELETE(false);
    setArticleDELETE(false);
    setArticleMODIFY(true);
    setArticleSelected(article);
    setArticleQuantite(article.quantite);
    setArticleQuantityError("");
    setCommentDraft(article.commentaire || "");
    setCommentEditingArticleId(article.id);
    showModal();
  };

  const handleDeleteArticle = (article) => {
    if (blockSignedEdit()) return;
    setDELETE(false);
    setArticleDELETE(true);
    setArticleMODIFY(false);
    setArticleSelected(article);
    showModal();
  };

  const handleDeleteDevis = () => {
    if (blockSignedEdit()) return;
    setDELETE(true);
    setArticleDELETE(false);
    setArticleMODIFY(false);
    showModal();
  };

  // ### Modify selected article in devis
  const modifyArticleWithComment = () => {
    if (blockSignedEdit()) return;
    const isQuantityValid = articleQuantityVerif(article_quantite);
    
    if (isQuantityValid){
      // Update quantity, comment, and recalculate amounts for immediate display
      const updatedArticles = articles_in_devis.map(article => {
        if (article.id === article_selected.id) {
          const unit_price = parseFloat(article.prix_vente_HT) || 0;
          const qty = parseFloat(article_quantite) || 0;
          const taux = parseFloat(article.taux_tva?.taux) || 0;
          
          const montant_HT = (unit_price * qty).toFixed(2);
          const montant_TVA = (unit_price * taux * qty).toFixed(2);
          const montant_TTC = (unit_price * (1 + taux) * qty).toFixed(2);
          
          return {
            ...article,
            quantite: qty,
            montant_HT: montant_HT,
            montant_TVA: montant_TVA,
            montant_TTC: montant_TTC,
            commentaire: commentDraft,
          };
        }
        return article;
      });
      setArticlesInDevis(updatedArticles);
      handleClose();
    }
  }

  const deleteArticle = () => {
    if (blockSignedEdit()) return;
    if (!article_selected || !article_selected.id) return;

    // Filter out the selected article
    const updatedArticles = articles_in_devis.filter(
      (article) => article.id !== article_selected.id
    );

    setArticlesInDevis(updatedArticles);
    handleClose();
  };


  // ### Add new article to devis ###
  const addNewArticle = async () => {
    if (blockSignedEdit()) return;
    const isQuantityValid = articleQuantityVerif(article_quantite);
    const isArticleSelected = article_selected.length !== 0;

    // If article is not already in the devis
    if (articles_in_devis.find(article => article.id === article_selected.id)) {
      showToast({ message: "Cet article est déjà dans le devis.", variant: "warning" });
      return;
    }

    // Set article in devis if inputs are valid
    if (isQuantityValid && isArticleSelected) {
      // Calculate amounts for immediate display
      const unit_price = parseFloat(article_selected.prix_vente_HT) || 0;
      const qty = parseFloat(article_quantite) || 0;
      const taux = parseFloat(article_selected.taux_tva?.taux) || 0;
      
      const montant_HT = (unit_price * qty).toFixed(2);
      const montant_TVA = (unit_price * taux * qty).toFixed(2);
      const montant_TTC = (unit_price * (1 + taux) * qty).toFixed(2);
      
      const newArticle = {
        ...article_selected,
        quantite: article_quantite,
        taux_tva: article_selected.taux_tva,
        montant_HT: montant_HT,
        montant_TVA: montant_TVA,
        montant_TTC: montant_TTC,
        commentaire: '',
      };

      // Add article to list
      setArticlesInDevis((prevArticles) => [...prevArticles, newArticle]);
      handleClose();
    }
  }

  // ### Save devis to database ###
  const saveDevis = async () => {
    if (blockSignedEdit()) return;
    if (isSaving) return; // Prevent duplicate submissions
    setIsSaving(true);
    setFormSubmited(true);
    const isTitleValid = devisTitleVerif(devis_title);
    const isDateValid = devisDateVerif(devis_date);
    const isContentValid = devisContentVerif(articles_in_devis);

    const isformValid = isTitleValid && isDateValid && isContentValid;

    if (isformValid){
      // Backend will compute amounts - we don't send client-calculated totals
      const devisData = {
        title: devis_title,
        description: devis_description,
        date: devis_date,
        remise: devis_remise,
        statut: devis_status,
        client_id: id_client,
        is_location: true,
        first_contribution_amount: first_contribution_amount,
        location_subscription_cost: location_subscription_cost,
        location_interests_cost: location_interests_cost,
        location_time: location_time,
        articles: articles_in_devis.map(article => ({
          article_id: article.id,
          quantite: article.quantite,
          taux_tva: article.taux_tva?.taux,
          commentaire: article.commentaire || null,
        })),
      };

      if (isNewDevis) {
        // Create new devis
        try {
        const resp = await httpClient.post(`${process.env.REACT_APP_BACKEND_URL}/devis/create`, devisData);
          const newDevisId = resp.data && resp.data.id;
          if (!newDevisId) {
            showToast({ message: "Erreur: id du devis manquant après création.", variant: "danger" });
            return;
          }
          
          // Update totals from API response
          if (resp.data.computed) {
            setDevisMontantHT(resp.data.computed.montant_ht);
            setDevisMontantTVA(resp.data.computed.montant_tva);
            setDevisMontantTTC(resp.data.computed.montant_ttc);
          }
          
          setIsNewDevis(false);
          
          // Fetch the newly created devis with retry logic
          let retries = 3;
          let fetchSuccess = false;
          
          while (retries > 0 && !fetchSuccess) {
            try {
              await new Promise(resolve => setTimeout(resolve, 300));
              const data = await fetchDevisById(newDevisId);
              if (data) {
                fetchSuccess = true;
                navigate(`/devis/${id_client}/${newDevisId}`, { replace: true });
              }
            } catch (error) {
              retries--;
              if (retries === 0) {
                showToast({ message: "Le devis a été créé mais il y a eu un problème lors du rechargement. Veuillez rafraîchir la page.", variant: "warning" });
                navigate(`/devis/${id_client}/${newDevisId}`, { replace: true });
              }
            }
          }
        } catch (error) {
          if (error.response && error.response.data && error.response.data.error) {
            showToast({ message: error.response.data.error, variant: "danger" });
          } else {
            showToast({ message: "Une erreur est survenue lors de la création du devis.", variant: "danger" });
          }
        } finally {
          setIsSaving(false);
        }
      } else {
        // Update existing devis
        try {
        const resp = await httpClient.put(`${process.env.REACT_APP_BACKEND_URL}/devis/update/${id_devis}`, devisData);
          // Update totals from API response
          if (resp.data.computed) {
            setDevisMontantHT(resp.data.computed.montant_ht);
            setDevisMontantTVA(resp.data.computed.montant_tva);
            setDevisMontantTTC(resp.data.computed.montant_ttc);
          }
          
          // Fetch the updated devis to get article amounts
          await fetchDevisById(id_devis);
          
          showToast({ message: "Devis enregistré avec succès.", variant: "success" });
        } catch (error) {
          if (error.response && error.response.data && error.response.data.error) {
            showToast({ message: error.response.data.error, variant: "danger" });
          } else {
            showToast({ message: "Une erreur est survenue lors de la mise à jour du devis.", variant: "danger" });
          }
        } finally {
          setIsSaving(false);
        }
      }
    } else {
      setIsSaving(false);
    }
  }

  // ### Save devis and generate PDF ###
  const handleGeneratePDF = async () => {
    // Allow PDF generation even for signed devis (no blockSignedEdit check)
    
    // For signed devis, just navigate to PDF without saving
    if (isLocked) {
      navigate(`/devis/${id_client}/${id_devis}/pdf`, { state: location.state });
      return;
    }

    // Validate form first for unsigned devis
    setFormSubmited(true);
    const isTitleValid = devisTitleVerif(devis_title);
    const isDateValid = devisDateVerif(devis_date);
    const isContentValid = devisContentVerif(articles_in_devis);
    const isformValid = isTitleValid && isDateValid && isContentValid;

    if (!isformValid) {
      showToast({ message: "Veuillez corriger les erreurs avant de générer le devis.", variant: "warning" });
      return;
    }

    // Save the devis (backend will compute amounts)
    const devisData = {
      title: devis_title,
      description: devis_description,
      date: devis_date,
      remise: devis_remise,
      statut: devis_status,
      client_id: id_client,
      is_location: true,
      first_contribution_amount: first_contribution_amount,
      location_subscription_cost: location_subscription_cost,
      location_interests_cost: location_interests_cost,
      location_time: location_time,
      articles: articles_in_devis.map(article => ({
        article_id: article.id,
        quantite: article.quantite,
        taux_tva: article.taux_tva?.taux,
        commentaire: article.commentaire || null,
      })),
    };

    try {
      const resp = await httpClient.put(`${process.env.REACT_APP_BACKEND_URL}/devis/update/${id_devis}`, devisData);
      // Update totals from API response
      if (resp.data.computed) {
        setDevisMontantHT(resp.data.computed.montant_ht);
        setDevisMontantTVA(resp.data.computed.montant_tva);
        setDevisMontantTTC(resp.data.computed.montant_ttc);
      }
      // Navigate to PDF page after saving
      navigate(`/devis/${id_client}/${id_devis}/pdf`, { state: location.state });
    } catch (error) {
      if (error.response && error.response.data && error.response.data.error) {
        showToast({ message: error.response.data.error, variant: "danger" });
      } else {
        showToast({ message: "Erreur lors de l'enregistrement du devis.", variant: "danger" });
      }
    }
  }

  // ### Delete devis from database ###
  const deleteDevis = async () => {
    if (blockSignedEdit()) return;
    const targetId = (devis && devis.id) ? devis.id : id_devis;
    if (!targetId) {
      showToast({ message: "Impossible de supprimer: aucun id de devis valide.", variant: "warning" });
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
          showToast({ message: error.response.data.error, variant: "danger" });
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
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
      setDevisRemise(data.remise || 0);
      setDevisStatus(data.statut);
      setSelectedScenario(data.selected_scenario || null); // load selected scenario if already chosen
      setFirstContributionAmount(data.first_contribution_amount || 0);

      if (Array.isArray(data.articles)) {
        setArticlesInDevis(
          data.articles.map((da) => {
            const taux = (da.taux_tva && da.taux_tva.taux != null) ? da.taux_tva.taux : da.article.taux_tva.taux;
            return {
              ...da.article,
              quantite: da.quantite,
              taux_tva: { taux },
              montant_HT: da.montant_HT || 0,
              montant_TVA: da.montant_TVA || 0,
              montant_TTC: da.montant_TTC || 0,
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
      if (error.response && error.response.data && error.response.data.error) {
        showToast({ message: error.response.data.error, variant: "danger" });
      } else {
        showToast({ message: "Une erreur est survenue lors du chargement du devis.", variant: "danger" });
      }
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
          showToast({ message: error.response.data.error, variant: "danger" });
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
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
            showToast({ message: error.response.data.error, variant: "danger" });
          }
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
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
        if (error.response && error.response.data && error.response.data.error) {
          showToast({ message: error.response.data.error, variant: "danger" });
        } else {
          showToast({ message: "Erreur lors du chargement des paramètres.", variant: "danger" });
        }
      });
  }

  const loadVatRates = async () => {
    try {
      const resp = await httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/devis/tva`);
      setVatRates(Array.isArray(resp.data?.data) ? resp.data.data : []);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.error) {
        showToast({ message: err.response.data.error, variant: "danger" });
      } else {
        showToast({ message: "Erreur lors du chargement des taux de TVA.", variant: "danger" });
      }
    }
  }

  const handleApportChange = (value) => {
    if (blockSignedEdit()) return;
    const apport = parseFloat(value) || 0;
    setFirstContributionAmount(apport);
  }

  const handleRemiseChange = (value) => {
    if (blockSignedEdit()) return;
    const parsed = parseFloat(value);
    const safeValue = !isNaN(parsed) && parsed >= 0 ? parsed : 0;
    setDevisRemise(safeValue);
  }

  useEffect(() => {
    getClientInfo();
    getAllArticles();
    getParameters();
    loadVatRates();
    // Only fetch if we have a valid devis ID
    if (id_devis && id_devis !== 'undefined') {
      fetchDevisById(id_devis).catch((err) => {
        if (!(err?.response && err.response.status === 404)) {
          console.error(err);
        }
      });
    } else {
      setIsNewDevis(true);
      setLoading(false);
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
    setDevisTitle(devis.titre);
    setDevisDescription(devis.description);
    setDevisDate(devis.date);
    setDevisMontantHT(devis.montant_HT);
    setDevisMontantTVA(devis.montant_TVA);
    setDevisMontantTTC(devis.montant_TTC);
    setDevisRemise(devis.remise || 0);
    setDevisStatus(devis.statut);
    setFirstContributionAmount(devis.first_contribution_amount || 0);

    if (Array.isArray(devis.articles)){
      setArticlesInDevis(
        devis.articles.map((da) => {
          const taux = (da.taux_tva && da.taux_tva.taux != null) ? da.taux_tva.taux : da.article.taux_tva.taux;
          return {
            ...da.article,
            quantite: da.quantite,
            taux_tva: { taux },
            montant_HT: da.montant_HT || 0,
            montant_TVA: da.montant_TVA || 0,
            montant_TTC: da.montant_TTC || 0,
            commentaire: da.commentaire || '',
          };
        })
      );
    }
    setLoading(false);
  }
}, [devis, isNewDevis]);

  // Recalculate totals when articles change (for immediate display before saving)
  useEffect(() => {
    if (loading) return;
    
    const totalHT = articles_in_devis.reduce((sum, article) => {
      return sum + (parseFloat(article.montant_HT) || 0);
    }, 0);
    
    const totalTVA = articles_in_devis.reduce((sum, article) => {
      return sum + (parseFloat(article.montant_TVA) || 0);
    }, 0);
    
    const totalTTC = articles_in_devis.reduce((sum, article) => {
      return sum + (parseFloat(article.montant_TTC) || 0);
    }, 0);
    
    setDevisMontantHT(totalHT.toFixed(2));
    setDevisMontantTVA(totalTVA.toFixed(2));
    setDevisMontantTTC(totalTTC.toFixed(2));
  }, [articles_in_devis, loading]);

  const modalTitle = DELETE
    ? 'Supprimer le devis'
    : article_DELETE
      ? "Supprimer l'article du devis"
      : article_MODIFY
        ? "Modifier la quantité de l'article"
        : "Ajouter un article";

  const modalBody = DELETE ? (
    <h5>
      Êtes-vous sur de vouloir supprimer le devis {devis && devis.titre} {client && `de ${client.nom.toUpperCase()} ${client.prenom}`}?
    </h5>
  ) : article_DELETE ? (
    <h5>Êtes-vous sur de vouloir supprimer l'article {article_selected?.nom} du devis ?</h5>
  ) : article_MODIFY ? (
    <div>
      <p>Modifier le nombre de {article_selected?.nom} :</p>
      <div className="form-outline col-md-6 mb-4">
        <input
          type="number"
          id="quantite"
          value={article_quantite}
          onChange={(e) => { setArticleQuantite(e.target.value); articleQuantityVerif(e.target.value); }}
          className={`form-control form-control-lg ${article_quantity_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
        />
        <div className="invalid-feedback">{article_quantity_error}</div>
      </div>
      <p className="mt-4">Ajouter un commentaire :</p>
      <div ref={commentEditorRef} style={{ minHeight: "150px", marginBottom: "1rem" }} />
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
            <th scope="col">Référence</th>
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
                <td><div dangerouslySetInnerHTML={{ __html: article.reference || "" }} style={{ lineHeight: '1.2' }} className="quill-content" /></td>
                <td>{article.prix_vente_HT?.toFixed(2) || '0.00'} €</td>
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
      <button className="btn btn-lg btn-success" onClick={modifyArticleWithComment}>Modifier</button>
    </div>
  ) : (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={handleClose}>Annuler</button>
      <button className="btn btn-lg btn-success" onClick={addNewArticle}>
        <PlusLg className="me-1" /> Ajouter
      </button>
    </div>
  );

  const totalTtcAfterRemise = Math.max((parseFloat(devis_montant_TTC) || 0) - (parseFloat(devis_remise) || 0), 0).toFixed(2);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <style>{`
        .quill-content p {
          margin: 0;
          padding: 0;
        }
        .quill-content ul, .quill-content ol {
          margin: 0;
          padding-left: 1.5em;
        }
      `}</style>
      <div className="d-flex justify-content-between align-items-start">
        <h1 className="mb-0">Devis N°{id_devis}</h1>
        <button className="btn btn-danger" onClick={goBack}>
          <ArrowReturnLeft className="me-1" /> Retour
        </button>
      </div>
      <br/>
      {client && (
        <>
          <h3>Client: {client.nom.toUpperCase()} {client.prenom}</h3>
          <h3>Adresse: {client.rue}, {client.code_postal} à {client.ville}</h3>
        </>
      )}
      <div className="row">
        <form className="col-lg-8 col-12">
          <div className="row">
            <div className="form-outline col-xl-4 col-6">
              <label className="form-label">Titre</label>
              <input type="text" id="titre" value={devis_title} onChange={(e) => {setDevisTitle(e.target.value);devisTitleVerif(e.target.value);}}
                className={`form-control form-control-lg ${devis_title_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un titre pour le devis" disabled={isLocked}/>
              <div className="invalid-feedback">{devis_title_error}</div>
            </div>
            <div className="form-outline col-xl-3 col-6">
              <label className="form-label">Date</label>
              <input type="date" id="date" value={devis_date} onChange={(e) => {setDevisDate(e.target.value);devisDateVerif(e.target.value);}}
                className={`form-control form-control-lg ${devis_date_error ? "is-invalid" : form_submited ? "is-valid": ""}`} disabled={isLocked}/>
              <div
              className="invalid-feedback">{devis_date_error}</div>
            </div>
          </div>
          <div className="row">
            <div className="form-outline col-xl-7 mt-4">
              <label className="form-label">Description</label>
              <textarea rows={3} id="description" value={devis_description} onChange={(e) => setDevisDescription(e.target.value)}
                className={`form-control form-control-lg`} placeholder="Entrer une description pour le devis" disabled={isLocked}/>
            </div>
          </div>
          {id_devis && (
            <div className="mt-4 d-flex flex-wrap align-items-center gap-3">
              <h3 className={`m-0 ${devis_status === "Non signé" || devis_status === "En attente de signature" ? "text-danger" : devis_status === "Signé" ? "text-success" : "text-warning"}`}>{devis_status}</h3>
              {selected_scenario && (
                <span className="badge bg-info">
                  Scénario sélectionné: <strong>{
                    selected_scenario === "direct" ? "Paiement direct" :
                    selected_scenario === "location_without_apport" ? "Location sans apport" :
                    selected_scenario === "location_with_apport" ? "Location avec apport" :
                    selected_scenario
                  }</strong>
                </span>
              )}
              {(devis_status === "Non signé" || devis_status === "En attente de signature") && (
                <div className="form-check mb-0 d-flex align-items-center gap-2">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    id="marquerSigne"
                    checked={devis_status === "Signé"}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setDevisStatus("Signé");
                        showToast({ message: "Devis marqué comme signé.", variant: "success" });
                      } else {
                        setDevisStatus("Non signé");
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
            <li className="nav-item" role="presentation">
              <button className={`nav-link ${isLocationDisabled ? 'disabled' : ''}`} id="location-tab" data-bs-toggle="tab" data-bs-target="#location-pane" type="button" role="tab" aria-controls="location-pane" aria-selected="false" disabled={isLocationDisabled}>
                Location
              </button>
            </li>
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
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="fw-bold fs-6">Montant total TTC:</span>
                <span className="ms-2 fw-bold">{devis_montant_TTC} €</span>
              </div>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="fw-bold">Remise (paiement direct):</span>
                <div className="d-flex align-items-center">
                  <input
                    type="number"
                    className="form-control form-control-sm"
                    style={{ width: '110px' }}
                    value={devis_remise}
                    onChange={(e) => handleRemiseChange(e.target.value)}
                    min="0"
                    step="0.01"
                    disabled={isLocked}
                  />
                  <span className="ms-2">€</span>
                </div>
              </div>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <span className="fw-bold fs-5">Total TTC après remise:</span>
                <span className="ms-2 fs-5 fw-bold">{totalTtcAfterRemise} €</span>
              </div>
            </div>

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
                    <input type="number" className="form-control form-control-sm" style={{width: '100px'}} value={isApportDisabled ? 0 : first_contribution_amount} onChange={(e) => handleApportChange(e.target.value)} step="0.01" min="0" disabled={isLocked || isApportDisabled} />
                    <span className="ms-2">€</span>
                  </div>
                </div>
            </div>
          </div>
        </div>
      </div>
      <div className="d-flex align-items-center mb-3 mt-4">
        <span className="me-3">TVA sélectionnée:</span>
        {vatRates.length === 0 ? (
          <span className="text-muted">Aucun taux disponible</span>
        ) : (
          vatRates.map((vat) => (
            <button
              key={vat.id}
              className="btn btn-outline-secondary me-2"
              onClick={() => applyVatToSelected(Number(vat.taux))}
              disabled={isLocked}
            >
              {(Number(vat.taux) * 100).toFixed(2).replace(/\.0+$/, "")}%
            </button>
          ))
        )}
      </div>
      <table className="table table-hover table-striped mt-4">
        <thead>
          <tr>
            <th scope="col"><input type="checkbox" checked={selectAllLines} onChange={toggleSelectAllLines} disabled={isLocked} style={{width: '20px', height: '20px', cursor: 'pointer'}} /></th>
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
                <td><input type="checkbox" checked={selectedArticleIds.includes(article.id)} onChange={() => toggleSelectLine(article.id)} disabled={isLocked} style={{width: '20px', height: '20px', cursor: 'pointer'}} /></td>
                <td onClick={() => { if (!isLocked) handleModifyArticle(article); }}>{article.nom}{(article.taux_tva?.taux ?? 0) === 0.10 ? ' (Rénovation)' : ''}</td>
                <td onClick={() => { if (!isLocked) handleModifyArticle(article); }}>{article.quantite}</td>
                <td onClick={() => { if (!isLocked) handleModifyArticle(article); }}>{((Number(article.taux_tva?.taux ?? 0)) * 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, '')}%</td>
                <td onClick={() => { if (!isLocked) handleModifyArticle(article); }}>{article.montant_HT} €</td>
                <td onClick={() => { if (!isLocked) handleModifyArticle(article); }}>{article.montant_TVA} €</td>
                <td onClick={() => { if (!isLocked) handleModifyArticle(article); }}>{article.montant_TTC} €</td>
                <td>
                  {article.commentaire ? (
                    <div dangerouslySetInnerHTML={{ __html: article.commentaire }} style={{ lineHeight: '1.2', fontSize: '0.9rem' }} className="quill-content" />
                  ) : (
                    <span className="text-muted small">Aucun commentaire</span>
                  )}
                </td>
                <td onClick={() => { if (!isLocked) handleDeleteArticle(article); }}><Trash3Fill color="red"/></td>
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
        <button className="btn btn-primary" onClick={handleAddArticle} disabled={isLocked}>
          <PlusLg className="me-1" /> Ajouter un article
        </button>
        <div>
          {!isNewDevis ? <button className="btn btn-danger me-4" onClick={handleDeleteDevis} disabled={isLocked}><Trash3Fill className="me-1" /> Supprimer le devis</button> : ""}
          {!isNewDevis ? <button className="btn btn-success me-4" onClick={handleGeneratePDF}><FileEarmarkPdf className="me-1" />Générer le devis</button> : ""}
          <button className="btn btn-success" onClick={saveDevis} disabled={(isLocked && !isNewDevis) || isSaving}>
            <FloppyFill className="me-1" /> {isSaving ? 'Enregistrement...' : 'Enregistrer le devis'}
          </button>
        </div>
      </div>
      <Modal
        ref={commentModalRef}
        title="Commentaire"
        size="modal-lg"
        footer={
          <>
            <button className="btn btn-secondary" onClick={closeCommentEditor}>
              Annuler
            </button>
            <button className="btn btn-primary" onClick={saveCommentEditor}>
              Enregistrer
            </button>
          </>
        }
      >
        <div ref={commentEditorRef} style={{ minHeight: "220px" }} />
      </Modal>
      <Modal ref={modalRef} title={modalTitle} footer={modalFooter} size="modal-lg" backdrop="static" keyboard={false}>
        {modalBody}
      </Modal>
    </div>
  );
}
export default Devis;