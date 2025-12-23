import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";
import { useToast } from "../components/Toast";

function AdminParameters() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [vats, setVats] = useState([]);
  const [newVat, setNewVat] = useState("");
  const [addingVat, setAddingVat] = useState(false);
  const [deletingVatId, setDeletingVatId] = useState(null);
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
  const { showToast } = useToast();

  // Fetch existing parameters when the page loads
  useEffect(() => {
    let isMounted = true;

    const fetchAll = async () => {
      try {
        const [paramsResp, tvaResp] = await Promise.all([
          httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/admin/parameters`),
          httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/admin/tva`),
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
      } catch (err) {
        if (!isMounted) return;
        console.error("Erreur lors du chargement des parametres", err);
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
    setErrorMessage("");
    try {
      await httpClient.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/parameters`,
        parameters
      );
      showToast({ message: "Parametres mis à jour", variant: "success" });
    } catch (err) {
      const message = err.response?.data?.error ?? "Une erreur est survenue.";
      setErrorMessage(message);
    } finally {
      setSaving(false);
    }
  };

  const handleAddVat = async () => {
    if (addingVat) return;
    const sanitized = String(newVat).replace(",", ".").replace(/[^0-9.]/g, "");
    const valuePercent = parseFloat(sanitized);
    if (Number.isNaN(valuePercent)) {
      setErrorMessage("Veuillez saisir un pourcentage valide (ex: 20 pour 20%)");
      return;
    }

    setAddingVat(true);
    setErrorMessage("");
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
      setErrorMessage(message);
    } finally {
      setAddingVat(false);
    }
  };

  const handleDeleteVat = async (id) => {
    if (!id || deletingVatId) return;
    // quick confirm to prevent accidental deletion
    const ok = window.confirm("Supprimer ce taux de TVA ?");
    if (!ok) return;
    setDeletingVatId(id);
    setErrorMessage("");
    try {
      await httpClient.delete(`${process.env.REACT_APP_BACKEND_URL}/admin/tva/${id}`);
      setVats((prev) => prev.filter((v) => v.id !== id));
      showToast({ message: "Taux TVA supprimé", variant: "success" });
    } catch (err) {
      const message = err.response?.data?.error ?? "Suppression impossible";
      setErrorMessage(message);
    } finally {
      setDeletingVatId(null);
    }
  };

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Parametres de l'application</h1>
      {errorMessage && (
        <div className="alert alert-danger" role="alert">
          {errorMessage}
        </div>
      )}
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
              <div className="col-md-6">
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
                    placeholder="20%"
                  />
                  <span className="input-group-text">%</span>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleAddVat}
                    disabled={addingVat}
                  >
                    {addingVat ? "Ajout..." : "Ajouter"}
                  </button>
                </div>
              </div>

              <div className="col-12">
                <h5 className="mt-2">Liste des taux de TVA</h5>
                {vats.length === 0 ? (
                  <p className="text-muted">Aucun taux enregistré.</p>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-striped table-bordered align-middle">
                      <thead>
                        <tr>
                          <th style={{ width: "120px" }}>ID</th>
                          <th>Taux</th>
                          <th style={{ width: "140px" }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {vats.map((vat) => (
                          <tr key={vat.id}>
                            <td>{vat.id}</td>
                            <td>{(Number(vat.taux) * 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, '')}%</td>
                            <td>
                              <button
                                type="button"
                                className="btn btn-sm btn-outline-danger"
                                onClick={() => handleDeleteVat(vat.id)}
                                disabled={deletingVatId === vat.id}
                              >
                                {deletingVatId === vat.id ? "Suppression..." : "Supprimer"}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="col-12 d-flex justify-content-end gap-2">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={() => window.history.back()}
            disabled={saving}
          >
            Retour
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Enregistrement..." : "Enregistrer"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default AdminParameters;
