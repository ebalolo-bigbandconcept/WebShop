import { useEffect, useState, useRef } from "react";
import httpClient from "../components/httpClient";
import { useToast } from "../components/Toast";
import {Trash3Fill, PlusLg, ArrowReturnLeft, FloppyFill} from "react-bootstrap-icons";
import Modal from "../components/Modal";

function AdminParameters() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [vats, setVats] = useState([]);
  const [newVat, setNewVat] = useState("");
  const [addingVat, setAddingVat] = useState(false);
  const [deletingVatId, setDeletingVatId] = useState(null);
  const [vatToDelete, setVatToDelete] = useState(null);
  const [DELETE, setDELETE] = useState(false);
  const [interestRates, setInterestRates] = useState([]);
  const [newInterestRate, setNewInterestRate] = useState({ minimum: "", maximum: "", interests: "" });
  const [addingInterestRate, setAddingInterestRate] = useState(false);
  const [deletingRateId, setDeletingRateId] = useState(null);
  const [editingRateId, setEditingRateId] = useState(null);
  const [editingRate, setEditingRate] = useState({ minimum: "", maximum: "", interests: "" });
  const [updatingRateId, setUpdatingRateId] = useState(null);
  const [rateToDelete, setRateToDelete] = useState(null);
  const [deleteType, setDeleteType] = useState(null);
  const modalRef = useRef(null);
  const { showToast } = useToast();
  const [parameters, setParameters] = useState({
    marginRate: "",
    marginRateLocation: "",
    locationTime: "",
    locationSubscriptionCost: "",
    locationInterestsCost: "",
    generalConditionsSales: "",
    companyName: "",
    companyAddressLine1: "",
    companyAddressLine2: "",
    companyZip: "",
    companyCity: "",
    companyPhone: "",
    companyEmail: "",
    companyIban: "",
    companyTva: "",
    companySiret: "",
    companyAprm: "",
  });
  const [activeTab, setActiveTab] = useState("enterprise");

  // Fetch existing parameters when the page loads
  useEffect(() => {
    let isMounted = true;

    const fetchAll = async () => {
      try {
        const [paramsResp, tvaResp, interestResp] = await Promise.all([
          httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/admin/parameters`),
          httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/admin/tva`),
          httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/admin/interest-rates`),
        ]);
        if (!isMounted) return;
        setParameters({
          marginRate: paramsResp.data?.marginRate ?? "",
          marginRateLocation: paramsResp.data?.marginRateLocation ?? "",
          locationTime: paramsResp.data?.locationTime ?? "",
          locationSubscriptionCost: paramsResp.data?.locationSubscriptionCost ?? "",
          locationInterestsCost: paramsResp.data?.locationInterestsCost ?? paramsResp.data?.locationMaintenanceCost ?? "",
          generalConditionsSales: paramsResp.data?.generalConditionsSales ?? "",
          companyName: paramsResp.data?.companyName ?? "",
          companyAddressLine1: paramsResp.data?.companyAddressLine1 ?? "",
          companyAddressLine2: paramsResp.data?.companyAddressLine2 ?? "",
          companyZip: paramsResp.data?.companyZip ?? "",
          companyCity: paramsResp.data?.companyCity ?? "",
          companyPhone: paramsResp.data?.companyPhone ?? "",
          companyEmail: paramsResp.data?.companyEmail ?? "",
          companyIban: paramsResp.data?.companyIban ?? "",
          companyTva: paramsResp.data?.companyTva ?? "",
          companySiret: paramsResp.data?.companySiret ?? "",
          companyAprm: paramsResp.data?.companyAprm ?? "",
        });
        setVats(tvaResp.data?.data ?? []);
        setInterestRates(interestResp.data?.data ?? []);
      } catch (err) {
        if (!isMounted) return;
        showToast({ message: "Erreur lors du chargement des paramètres", variant: "danger" });
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchAll();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleChange = (key) => (e) => {
    setParameters((prev) => ({ ...prev, [key]: e.target.value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await httpClient.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/parameters`,
        parameters
      );
      showToast({ message: "Parametres mis à jour", variant: "success" });
    } catch (err) {
      const message = err.response?.data?.error ?? "Une erreur est survenue.";
      showToast({ message, variant: "danger" });
    } finally {
      setSaving(false);
    }
  };

  const handleAddVat = async () => {
    if (addingVat) return;
    const sanitized = String(newVat).replace(",", ".").replace(/[^0-9.]/g, "");
    const valuePercent = parseFloat(sanitized);
    if (Number.isNaN(valuePercent)) {
      showToast({ message: "Veuillez saisir un pourcentage valide (ex: 20 pour 20%)", variant: "danger" });
      return;
    }

    setAddingVat(true);
    try {
      const resp = await httpClient.post(`${process.env.REACT_APP_BACKEND_URL}/admin/tva`, {
        taux: valuePercent / 100,
      });
      setVats((prev) => {
        const already = prev.find((v) => v.id === resp.data.id);
        if (already) return prev;
        return [...prev, resp.data].sort((a, b) => a.id - b.id);
      });
      setNewVat("");
      showToast({ message: "Taux TVA ajouté", variant: "success" });
    } catch (err) {
      const message = err.response?.data?.error ?? "Impossible d'ajouter le taux";
      showToast({ message, variant: "danger" });
    } finally {
      setAddingVat(false);
    }
  };

  const handleDeleteVat = async (vatId, vatTaux) => {
    setDeleteType("vat");
    setVatToDelete({ id: vatId, taux: vatTaux });
    setDELETE(true);
    showModal();
  };

  const showModal = () => {
    modalRef.current && modalRef.current.open();
  };

  const handleCloseModal = () => {
    modalRef.current && modalRef.current.close();
    setDELETE(false);
    setVatToDelete(null);
    setRateToDelete(null);
    setDeleteType(null);
  };

  const deleteVat = async () => {
    if (!vatToDelete || deletingVatId) return;
    setDeletingVatId(vatToDelete.id);
    try {
      await httpClient.delete(`${process.env.REACT_APP_BACKEND_URL}/admin/tva/${vatToDelete.id}`);
      setVats((prev) => prev.filter((v) => v.id !== vatToDelete.id));
      showToast({ message: "Taux TVA supprimé", variant: "success" });
      handleCloseModal();
    } catch (err) {
      const message = err.response?.data?.error ?? "Suppression impossible";
      showToast({ message, variant: "danger" });
    } finally {
      setDeletingVatId(null);
    }
  };

  // Interest Rate Handlers
  const handleAddInterestRate = async () => {
    if (addingInterestRate) return;
    
    const minimum = parseFloat(newInterestRate.minimum);
    const maximum = parseFloat(newInterestRate.maximum);
    const interests = parseFloat(newInterestRate.interests);

    if (Number.isNaN(minimum) || Number.isNaN(maximum) || Number.isNaN(interests)) {
      showToast({ message: "Veuillez remplir tous les champs avec des nombres valides", variant: "danger" });
      return;
    }

    if (minimum >= maximum) {
      showToast({ message: "Le minimum doit être inférieur au maximum (ex: 0-999, 1000-1999)", variant: "danger" });
      return;
    }

    // Check for overlapping ranges
    const overlap = interestRates.find(
      (rate) => minimum <= rate.maximum && rate.minimum <= maximum
    );
    if (overlap) {
      showToast({
        message: `Cette plage chevauche une plage existante (${overlap.minimum}-${overlap.maximum}).`,
        variant: "danger"
      });
      return;
    }

    setAddingInterestRate(true);
    try {
      const resp = await httpClient.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/interest-rates`,
        {
          minimum,
          maximum,
          interests,
        }
      );
      setInterestRates((prev) => [...prev, resp.data].sort((a, b) => a.minimum - b.minimum));
      setNewInterestRate({ minimum: "", maximum: "", interests: "" });
      showToast({ message: "Plage de taux d'intérêt ajoutée", variant: "success" });
    } catch (err) {
      const message = err.response?.data?.error ?? "Impossible d'ajouter la plage";
      showToast({ message, variant: "danger" });
    } finally {
      setAddingInterestRate(false);
    }
  };

  const handleDeleteInterestRate = async (rateId) => {
    setDeleteType("rate");
    setRateToDelete(rateId);
    setDELETE(true);
    showModal();
  };

  const deleteInterestRate = async () => {
    if (!rateToDelete || deletingRateId) return;
    setDeletingRateId(rateToDelete);
    try {
      await httpClient.delete(`${process.env.REACT_APP_BACKEND_URL}/admin/interest-rates/${rateToDelete}`);
      setInterestRates((prev) => prev.filter((r) => r.id !== rateToDelete));
      showToast({ message: "Plage supprimée", variant: "success" });
      handleCloseModal();
    } catch (err) {
      const message = err.response?.data?.error ?? "Suppression impossible";
      showToast({ message, variant: "danger" });
    } finally {
      setDeletingRateId(null);
    }
  };

  const handleStartEdit = (rate) => {
    setEditingRateId(rate.id);
    setEditingRate({
      minimum: rate.minimum,
      maximum: rate.maximum,
      interests: rate.interests,
    });
  };

  const handleUpdateInterestRate = async () => {
    if (updatingRateId || !editingRateId) return;

    const minimum = parseFloat(editingRate.minimum);
    const maximum = parseFloat(editingRate.maximum);
    const interests = parseFloat(editingRate.interests);

    if (Number.isNaN(minimum) || Number.isNaN(maximum) || Number.isNaN(interests)) {
      showToast({ message: "Veuillez remplir tous les champs avec des nombres valides", variant: "danger" });
      return;
    }

    if (minimum >= maximum) {
      showToast({ message: "Le minimum doit être inférieur au maximum (ex: 0-999, 1000-1999)", variant: "danger" });
      return;
    }

    // Check for overlapping ranges (excluding the current rate being edited)
    const overlap = interestRates.find(
      (rate) => rate.id !== editingRateId && minimum <= rate.maximum && rate.minimum <= maximum
    );
    if (overlap) {
      showToast({
        message: `Cette plage chevauche une plage existante (${overlap.minimum}-${overlap.maximum}).`,
        variant: "danger"
      });
      return;
    }

    setUpdatingRateId(editingRateId);
    try {
      const resp = await httpClient.put(
        `${process.env.REACT_APP_BACKEND_URL}/admin/interest-rates/${editingRateId}`,
        {
          minimum,
          maximum,
          interests,
        }
      );
      setInterestRates((prev) =>
        prev.map((r) => (r.id === editingRateId ? resp.data : r)).sort((a, b) => a.minimum - b.minimum)
      );
      setEditingRateId(null);
      setEditingRate({ minimum: "", maximum: "", interests: "" });
      showToast({ message: "Plage mise à jour", variant: "success" });
    } catch (err) {
      const message = err.response?.data?.error ?? "Mise à jour impossible";
      showToast({ message, variant: "danger" });
    } finally {
      setUpdatingRateId(null);
    }
  };

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <div className="d-flex justify-content-between align-items-start mb-3">
        <h1>Parametres de l'application</h1>
        <br/>

        <button
          type="button"
          className="btn btn-danger"
          onClick={() => window.history.back()}
          disabled={saving}
        >
          <ArrowReturnLeft className="me-1" /> Retour
        </button>
      </div>
      <form className="row g-3" onSubmit={handleSave}>
        <ul className="nav nav-tabs mb-3">
          <li className="nav-item">
            <button
              type="button"
              className={`nav-link ${activeTab === "enterprise" ? "active" : ""}`}
              onClick={() => setActiveTab("enterprise")}
            >
              Entreprise
            </button>
          </li>
          <li className="nav-item">
            <button
              type="button"
              className={`nav-link ${activeTab === "devis" ? "active" : ""}`}
              onClick={() => setActiveTab("devis")}
            >
              Devis
            </button>
          </li>
          <li className="nav-item">
            <button
              type="button"
              className={`nav-link ${activeTab === "tva" ? "active" : ""}`}
              onClick={() => setActiveTab("tva")}
            >
              TVA
            </button>
          </li>
          <li className="nav-item">
            <button
              type="button"
              className={`nav-link ${activeTab === "interests" ? "active" : ""}`}
              onClick={() => setActiveTab("interests")}
            >
              Intérêts
            </button>
          </li>
        </ul>

        <div className="tab-content w-100">
          <div className={`tab-pane fade ${activeTab === "enterprise" ? "show active" : ""}`}>
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label">Nom de l'entreprise</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyName}
                  onChange={handleChange("companyName")}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Adresse (ligne 1)</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyAddressLine1}
                  onChange={handleChange("companyAddressLine1")}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Adresse (ligne 2)</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyAddressLine2}
                  onChange={handleChange("companyAddressLine2")}
                />
              </div>
              <div className="col-md-3">
                <label className="form-label">Code postal</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyZip}
                  onChange={handleChange("companyZip")}
                />
              </div>
              <div className="col-md-3">
                <label className="form-label">Ville</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyCity}
                  onChange={handleChange("companyCity")}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Téléphone</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyPhone}
                  onChange={handleChange("companyPhone")}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-control"
                  value={parameters.companyEmail}
                  onChange={handleChange("companyEmail")}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Siret</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companySiret}
                  onChange={handleChange("companySiret")}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">TVA</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyTva}
                  onChange={handleChange("companyTva")}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">IBAN</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyIban}
                  onChange={handleChange("companyIban")}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">APRM</label>
                <input
                  type="text"
                  className="form-control"
                  value={parameters.companyAprm}
                  onChange={handleChange("companyAprm")}
                />
              </div>
            </div>
          </div>

          <div className={`tab-pane fade ${activeTab === "devis" ? "show active" : ""}`}>
            <div className="row g-3">
              <div className="col-md-6">
                <label className="form-label">Taux de marge (x Prix de vente)</label>
                <input
                  type="number"
                  className="form-control"
                  value={parameters.marginRate}
                  onChange={handleChange("marginRate")}
                  min="0"
                  step="0.1"
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Taux de marge de location (x Prix de vente)</label>
                <input
                  type="number"
                  className="form-control"
                  value={parameters.marginRateLocation}
                  onChange={handleChange("marginRateLocation")}
                  min="0"
                  step="0.1"
                />
              </div>
              <div className="col-md-4">
                <label className="form-label">Temps de location (mois)</label>
                <input
                  type="number"
                  className="form-control"
                  value={parameters.locationTime}
                  onChange={handleChange("locationTime")}
                  min="0"
                  step="1"
                />
              </div>
              <div className="col-md-4">
                <label className="form-label">Coût d'abonement de location (EUR)</label>
                <input
                  type="number"
                  className="form-control"
                  value={parameters.locationSubscriptionCost}
                  onChange={handleChange("locationSubscriptionCost")}
                  min="0"
                  step="0.1"
                />
              </div>
              <div className="col-md-4">
                <label className="form-label">Intérêts de la location (EUR)</label>
                <input
                  type="number"
                  className="form-control"
                  value={parameters.locationInterestsCost}
                  onChange={handleChange("locationInterestsCost")}
                  min="0"
                  step="0.1"
                />
              </div>
              <div className="col-12">
                <label className="form-label">Conditions générales de vente</label>
                <textarea
                  className="form-control"
                  value={parameters.generalConditionsSales}
                  onChange={handleChange("generalConditionsSales")}
                  rows="6"
                ></textarea>
              </div>
            </div>
          </div>

          <div className={`tab-pane fade ${activeTab === "tva" ? "show active" : ""}`}>
            <div className="row g-3">
              <div className="col-2">
                <h5>Liste des taux de TVA</h5>
                {vats.length === 0 ? (
                  <p className="text-muted">Aucun taux enregistré.</p>
                ) : (
                  <table className="table table-hover table-striped">
                    <thead>
                      <tr>
                        <th scope="col">ID</th>
                        <th scope="col">Taux</th>
                        <th scope="col"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {vats.map((vat) => (
                        <tr key={vat.id}>
                          <td>{vat.id}</td>
                          <td>{(Number(vat.taux) * 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, '')}%</td>
                          <td>
                            <Trash3Fill
                              color="red"
                              style={{ cursor: "pointer" }}
                              onClick={() => handleDeleteVat(vat.id, (Number(vat.taux) * 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, ''))}
                              title="Supprimer ce taux de TVA"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="col-2">
                <label className="form-label">Ajouter un taux de TVA</label>
                <div className="input-group">
                  <input
                    type="number"
                    className="form-control"
                    value={newVat}
                    onChange={(e) => setNewVat(e.target.value)}
                    step="1"
                    min="0"
                    max="100"
                    placeholder="20"
                  />
                  <span className="input-group-text">%</span>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleAddVat}
                    disabled={addingVat}
                  >
                    {addingVat ? "Ajout..." : (
                      <>
                        <PlusLg className="me-1" /> Ajouter
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className={`tab-pane fade ${activeTab === "interests" ? "show active" : ""}`}>
            <div className="row g-3">
              <div className="col-12">
                <h5>Ajouter une nouvelle plage</h5>
                <div className="row g-2">
                  <div className="col-md-3">
                    <label className="form-label">Minimum</label>
                    <input
                      type="number"
                      className="form-control"
                      value={newInterestRate.minimum}
                      onChange={(e) =>
                        setNewInterestRate({ ...newInterestRate, minimum: e.target.value })
                      }
                      step="0.01"
                      min="0"
                      placeholder="0"
                    />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Maximum</label>
                    <input
                      type="number"
                      className="form-control"
                      value={newInterestRate.maximum}
                      onChange={(e) =>
                        setNewInterestRate({ ...newInterestRate, maximum: e.target.value })
                      }
                      step="0.01"
                      min="0"
                      placeholder="999"
                    />
                  </div>
                  <div className="col-md-3">
                    <label className="form-label">Intérêts (EUR)</label>
                    <input
                      type="number"
                      className="form-control"
                      value={newInterestRate.interests}
                      onChange={(e) =>
                        setNewInterestRate({ ...newInterestRate, interests: e.target.value })
                      }
                      step="1"
                      min="0"
                      placeholder="500"
                    />
                  </div>
                  <div className="col-md-3 d-flex align-items-end">
                    <button
                      type="button"
                      className="btn btn-primary w-100"
                      onClick={handleAddInterestRate}
                      disabled={addingInterestRate || editingRateId !== null}
                    >
                      {addingInterestRate ? "Ajout..." : (
                        <>
                          <PlusLg className="me-1" /> Ajouter
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              <div className="col-12">
                <h5>Plages de taux d'intérêt</h5>
                <table className="table table-hover table-striped">
                  <thead>
                    <tr>
                      <th scope="col">Minimum</th>
                      <th scope="col">Maximum</th>
                      <th scope="col">Intérêts (EUR)</th>
                      <th scope="col"></th>
                      <th scope="col"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {interestRates.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="text-center text-muted">
                          Aucune plage enregistrée.
                        </td>
                      </tr>
                    ) : (
                      interestRates.map((rate) => (
                        <tr key={rate.id}>
                          {editingRateId === rate.id ? (
                            <>
                              <td>
                                <input
                                  type="number"
                                  className="form-control form-control-sm"
                                  value={editingRate.minimum}
                                  onChange={(e) =>
                                    setEditingRate({ ...editingRate, minimum: e.target.value })
                                  }
                                  step="0.01"
                                  min="0"
                                />
                              </td>
                              <td>
                                <input
                                  type="number"
                                  className="form-control form-control-sm"
                                  value={editingRate.maximum}
                                  onChange={(e) =>
                                    setEditingRate({ ...editingRate, maximum: e.target.value })
                                  }
                                  step="0.01"
                                  min="0"
                                />
                              </td>
                              <td>
                                <input
                                  type="number"
                                  className="form-control form-control-sm"
                                  value={editingRate.interests}
                                  onChange={(e) =>
                                    setEditingRate({ ...editingRate, interests: e.target.value })
                                  }
                                  step="0.1"
                                  min="0"
                                />
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-success"
                                  onClick={handleUpdateInterestRate}
                                  disabled={updatingRateId !== null}
                                >
                                  Sauvegarder
                                </button>
                              </td>
                              <td>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-secondary"
                                  onClick={() => setEditingRateId(null)}
                                  disabled={updatingRateId !== null}
                                >
                                  Annuler
                                </button>
                              </td>
                            </>
                          ) : (
                            <>
                              <td 
                                style={{ cursor: "pointer" }}
                                onClick={() => handleStartEdit(rate)}
                                disabled={editingRateId !== null || updatingRateId !== null}
                              >
                                {rate.minimum.toLocaleString('fr-FR')}
                              </td>
                              <td 
                                style={{ cursor: "pointer" }}
                                onClick={() => handleStartEdit(rate)}
                                disabled={editingRateId !== null || updatingRateId !== null}
                              >
                                {rate.maximum.toLocaleString('fr-FR')}
                              </td>
                              <td 
                                style={{ cursor: "pointer" }}
                                onClick={() => handleStartEdit(rate)}
                                disabled={editingRateId !== null || updatingRateId !== null}
                              >
                                {rate.interests.toLocaleString('fr-FR')} €
                              </td>
                              <td></td>
                              <td>
                                <Trash3Fill
                                  color="red"
                                  style={{ cursor: "pointer" }}
                                  onClick={() => handleDeleteInterestRate(rate.id)}
                                  title="Supprimer cette plage"
                                />
                              </td>
                            </>
                          )}
                        </tr>
                      ))
                    )}
                    </tbody>
                  </table>
              </div>
            </div>
          </div>
        </div>
        {activeTab !== "tva" && activeTab !== "interests" &&
        <div className="col-12 d-flex justify-content-end gap-2">
          <button type="submit" className="btn btn-success" disabled={saving}>
            {saving ? "Enregistrement..." : (
              <>
                <FloppyFill className="me-1" /> Enregistrer
              </>
            )}
          </button>
        </div>
        }
      </form>

      <Modal 
        ref={modalRef}
        title={DELETE ? (deleteType === "vat" ? "Supprimer un taux de TVA" : "Supprimer une plage d'intérêt") : ""}
        footer={DELETE ? (
          <div className="d-flex justify-content-between w-100">
            <button className="btn btn-lg btn-danger" onClick={handleCloseModal}>Annuler</button>
            <button 
              className="btn btn-lg btn-success" 
              onClick={deleteType === "vat" ? deleteVat : deleteInterestRate}
              disabled={deleteType === "vat" ? deletingVatId !== null : deletingRateId !== null}
            >
              Supprimer
            </button>
          </div>
        ) : null}
      >
        {DELETE && deleteType === "vat" && vatToDelete ? (
          <h5>Êtes-vous sûr de vouloir supprimer le taux TVA "{vatToDelete.taux}%" ?</h5>
        ) : null}
        {DELETE && deleteType === "rate" && rateToDelete ? (
          <h5>Êtes-vous sûr de vouloir supprimer cette plage d'intérêt ?</h5>
        ) : null}
      </Modal>

    </div>
  );
}

export default AdminParameters;
