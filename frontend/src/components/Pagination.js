import React from 'react';

function Pagination({ currentPage, totalPages, onPageChange }) {
  if (totalPages <= 1) return null;

  // Calculate which page numbers to show
  const getPageNumbers = () => {
    const delta = 2; // Show 2 pages before and after current
    const left = currentPage - delta;
    const right = currentPage + delta;

    let pages = [];

    // Always show first page
    pages.push(1);

    // Add ellipsis and pages before current
    if (left > 2) {
      pages.push('...');
    }
    for (let i = Math.max(2, left); i <= Math.min(totalPages - 1, right); i++) {
      pages.push(i);
    }

    // Add ellipsis and last page
    if (right < totalPages - 1) {
      pages.push('...');
    }
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  };

  const pageNumbers = getPageNumbers();

  return (
    <nav>
      <ul className="pagination justify-content-center">
        <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
          <a
            className="page-link"
            href="!#"
            onClick={(e) => {
              e.preventDefault();
              if (currentPage > 1) onPageChange(currentPage - 1);
            }}
          >
            Précédent
          </a>
        </li>

        {pageNumbers.map((number, index) => {
          if (number === '...') {
            return (
              <li key={`ellipsis-${index}`} className="page-item disabled">
                <span className="page-link">...</span>
              </li>
            );
          }
          return (
            <li
              key={number}
              className={`page-item ${currentPage === number ? 'active' : ''}`}
            >
              <a
                onClick={(e) => {
                  e.preventDefault();
                  onPageChange(number);
                }}
                href="!#"
                className="page-link"
              >
                {number}
              </a>
            </li>
          );
        })}

        <li className={`page-item ${currentPage >= totalPages ? 'disabled' : ''}`}>
          <a
            className="page-link"
            href="!#"
            onClick={(e) => {
              e.preventDefault();
              if (currentPage < totalPages) onPageChange(currentPage + 1);
            }}
          >
            Suivant
          </a>
        </li>
      </ul>
    </nav>
  );
}

export default Pagination;
