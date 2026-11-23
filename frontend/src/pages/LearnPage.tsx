import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { get } from "../api/client";
import type { ArticleFull } from "../api/types";
import { BookOpen } from "../components/icons";
import { Modal } from "../components/Modal";
import { Badge, EmptyState, Loading, PageHeader } from "../components/ui";

const CATEGORIES = ["all", "health", "nutrition", "development", "safety", "parenting", "learning"];

export default function LearnPage() {
  const [category, setCategory] = useState("all");
  const [open, setOpen] = useState<ArticleFull | null>(null);
  const articles = useQuery({ queryKey: ["articles"], queryFn: () => get<ArticleFull[]>("/content/articles") });
  const list = articles.data?.filter((a) => a.status === "published" && (category === "all" || a.category === category));

  return (
    <>
      <PageHeader title="Guidance for parents" subtitle="Reviewed articles on health, nutrition and development." />
      <div className="chips" style={{ marginBottom: 18 }}>
        {CATEGORIES.map((c) => (
          <label key={c} className={`chip ${category === c ? "on" : ""}`} style={{ textTransform: "capitalize" }}>
            <input type="radio" checked={category === c} onChange={() => setCategory(c)} />
            {c}
          </label>
        ))}
      </div>
      {articles.isLoading && <Loading rows={4} />}
      {list?.length === 0 && <EmptyState title="Nothing here yet" icon={<BookOpen size={22} />} />}
      <div className="grid grid-3">
        {list?.map((a) => (
          <article key={a.id} className="card article-card clickable" onClick={() => setOpen(a)}>
            <div className="article-cover">{a.cover_image_url ? <img src={a.cover_image_url} alt="" /> : <BookOpen size={32} />}</div>
            <div className="card-body">
              <Badge value={a.category} />
              <h3>{a.title}</h3>
              <p className="muted small">{a.summary}</p>
            </div>
          </article>
        ))}
      </div>
      {open && (
        <Modal title={open.title} onClose={() => setOpen(null)} wide>
          {open.cover_image_url && <img src={open.cover_image_url} alt="" style={{ width: "100%", borderRadius: 12, marginBottom: 14 }} />}
          <Badge value={open.category} />
          <p style={{ whiteSpace: "pre-wrap", marginTop: 12 }}>{open.body}</p>
        </Modal>
      )}
    </>
  );
}
