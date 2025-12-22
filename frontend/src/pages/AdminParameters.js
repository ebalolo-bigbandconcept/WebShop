import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";

function AdminParameters() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
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

    const fetchParameters = async () => {
      try {
        const resp = await httpClient.get(
          `${process.env.REACT_APP_BACKEND_URL}/admin/parameters`
        );
        if (!isMounted) return;
        setParameters({
          marginRate: resp.data?.marginRate ?? "",
          marginRateLocation: resp.data?.marginRateLocation ?? "",
          locationTime: resp.data?.locationTime ?? "",
          locationSubscriptionCost: resp.data?.locationSubscriptionCost ?? "",
          locationInterestsCost: resp.data?.locationInterestsCost ?? resp.data?.locationMaintenanceCost ?? "",
          generalConditionsSales: resp.data?.generalConditionsSales ?? "",
          companyName: resp.data?.companyName ?? "",
          companyAddressLine1: resp.data?.companyAddressLine1 ?? "",
          companyAddressLine2: resp.data?.companyAddressLine2 ?? "",
          companyZip: resp.data?.companyZip ?? "",
          companyCity: resp.data?.companyCity ?? "",
          companyPhone: resp.data?.companyPhone ?? "",
          companyEmail: resp.data?.companyEmail ?? "",
          companyIban: resp.data?.companyIban ?? "",
          companyTva: resp.data?.companyTva ?? "",
          companySiret: resp.data?.companySiret ?? "",
          companyAprm: resp.data?.companyAprm ?? "",
        });
      } catch (err) {
        if (!isMounted) return;
        console.error("Erreur lors du chargement des parametres", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchParameters();
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
      alert("Parametres mis a jour");
    } catch (err) {
      const message = err.response?.data?.error ?? "Une erreur est survenue.";
      setErrorMessage(message);
    } finally {
      setSaving(false);
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
