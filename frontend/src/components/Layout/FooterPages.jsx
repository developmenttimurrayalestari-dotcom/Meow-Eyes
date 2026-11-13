import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../lib/api';
import { cmsPagePath } from '../../lib/cmsPages';

export default function FooterPages() {
  const [pages, setPages] = useState([]);
  useEffect(() => {
    const controller = new AbortController();
    api.get('/pages', { signal: controller.signal }).then(({ data }) => {
      if (!controller.signal.aborted) setPages(data.pages || []);
    }).catch(() => { /* Other help links remain usable if CMS navigation is unavailable. */ });
    return () => controller.abort();
  }, []);
  return pages.filter(page => page.slug && page.title).map(page => <li key={page.id || page.slug}>
    <Link to={cmsPagePath(page.slug)} data-testid={page.page_type === 'terms_conditions' ? 'footer-terms' : page.page_type === 'privacy_policy' ? 'footer-privacy' : `footer-page-${page.slug}`}>{page.title}</Link>
  </li>);
}
