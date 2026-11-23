import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { del, get, patch, post, upload } from "../../api/client";
import type { ArticleFull } from "../../api/types";
import { BookOpen, Image, Pencil, Plus, Trash2 } from "../../components/icons";
import { Modal } from "../../components/Modal";
import { useToast } from "../../components/Toast";
import { Badge, Button, Card, EmptyState, ErrorText, Field, Loading, PageHeader, Tabs } from "../../components/ui";
import { formatDate } from "../../utils/format";

const CATEGORIES = ["parenting", "nutrition", "development", "health", "safety", "learning"];
type Filter = "all" | ArticleFull["status"];

const slugify = (s: string) => s.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 160);

export default function ContentPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const [filter, setFilter] = useState<Filter>("all");
  const [editing, setEditing] = useState<ArticleFull | "new" | null>(null);
  const articles = useQuery({ queryKey: ["articles"], queryFn: () => get<ArticleFull[]>("/content/articles") });
  const list = articles.data?.filter((a) => filter === "all" || a.status === filter);
  const refresh = () => qc.invalidateQueries({ queryKey: ["articles"] });

  const setStatus = useMutation({
    mutationFn: ({ a, status }: { a: ArticleFull; status: ArticleFull["status"] }) => patch(`/content/articles/${a.id}`, { status }),
    onSuccess: (_, { status }) => { refresh(); toast(status === "published" ? "Article published" : "Status updated"); },
    onError: (e) => toast(e.message, "error"),
  });
  const remove = useMutation({
    mutationFn: (a: ArticleFull) => del(`/content/articles/${a.id}`),
    onSuccess: () => { refresh(); toast("Article deleted"); },
  });
  const count = (f: Filter) => articles.data?.filter((a) => f === "all" || a.status === f).length ?? 0;

  return (
    <>
      <PageHeader
        title="Content"
        subtitle="Guidance articles for parents. Health articles must be published by a health reviewer or admin."
        actions={<Button icon={<Plus size={16} />} onClick={() => setEditing("new")}>New article</Button>}
      />
      <Tabs<Filter>
        value={filter}
        onChange={setFilter}
        tabs={[
          { value: "all", label: `All (${count("all")})` },
          { value: "published", label: `Published (${count("published")})` },
          { value: "in_review", label: `In review (${count("in_review")})` },
          { value: "draft", label: `Drafts (${count("draft")})` },
          { value: "archived", label: `Archived (${count("archived")})` },
        ]}
      />
      <Card flush>
        {articles.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
        {list?.length === 0 && <EmptyState title="No articles" icon={<BookOpen size={22} />} />}
        {!!list?.length && (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Article</th><th>Category</th><th>Status</th><th>Published</th><th /></tr></thead>
              <tbody>
                {list.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <div className="row" style={{ flexWrap: "nowrap", gap: 12 }}>
                        <div className="avatar" style={{ borderRadius: 10, background: "var(--surface-2)", color: "var(--text-3)" }}>
                          {a.cover_image_url ? <img src={a.cover_image_url} alt="" /> : <Image size={16} />}
                        </div>
                        <div>
                          <div className="strong">{a.title}</div>
                          <div className="muted small">/{a.slug}</div>
                        </div>
                      </div>
                    </td>
                    <td><Badge value={a.category} /></td>
                    <td><Badge value={a.status} /></td>
                    <td className="small">{formatDate(a.published_at)}</td>
                    <td>
                      <div className="row" style={{ flexWrap: "nowrap", gap: 4 }}>
                        {a.status !== "published" ? (
                          <Button size="sm" onClick={() => setStatus.mutate({ a, status: "published" })}>Publish</Button>
                        ) : (
                          <Button size="sm" variant="secondary" onClick={() => setStatus.mutate({ a, status: "archived" })}>Archive</Button>
                        )}
                        <Button variant="ghost" size="sm" aria-label="Edit" onClick={() => setEditing(a)}><Pencil size={15} /></Button>
                        <Button variant="ghost" size="sm" aria-label="Delete" onClick={() => confirm(`Delete “${a.title}”?`) && remove.mutate(a)}><Trash2 size={15} /></Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      {editing && (
        <ArticleForm
          article={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => { refresh(); setEditing(null); toast("Article saved"); }}
        />
      )}
    </>
  );
}

function ArticleForm({ article, onClose, onSaved }: { article: ArticleFull | null; onClose: () => void; onSaved: () => void }) {
  const [title, setTitle] = useState(article?.title ?? "");
  const [slug, setSlug] = useState(article?.slug ?? "");
  const [summary, setSummary] = useState(article?.summary ?? "");
  const [body, setBody] = useState(article?.body ?? "");
  const [category, setCategory] = useState(article?.category ?? "parenting");
  const [cover, setCover] = useState<File | null>(null);

  const save = useMutation({
    mutationFn: async () => {
      const data = { title, summary, body, category };
      const saved = article
        ? await patch<ArticleFull>(`/content/articles/${article.id}`, data)
        : await post<ArticleFull>("/content/articles", { ...data, slug: slug || slugify(title), audience: "parent" });
      if (cover) await upload(`/content/articles/${saved.id}/cover`, cover);
    },
    onSuccess: onSaved,
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate();
  }

  return (
    <Modal
      wide
      title={article ? "Edit article" : "New article"}
      onClose={onClose}
      footer={<><Button variant="ghost" onClick={onClose}>Cancel</Button><Button form="article-form" disabled={save.isPending}>{save.isPending ? "Saving…" : "Save"}</Button></>}
    >
      <form id="article-form" className="form" onSubmit={submit}>
        <div className="form-grid">
          <Field label="Title"><input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} /></Field>
          <Field label="Category">
            <select className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c[0].toUpperCase() + c.slice(1)}</option>)}
            </select>
          </Field>
        </div>
        {!article && (
          <Field label="URL slug" hint={`Leave empty to use “${slugify(title) || "generated-from-title"}”`}>
            <input className="input mono" value={slug} onChange={(e) => setSlug(slugify(e.target.value))} />
          </Field>
        )}
        <Field label="Summary"><input className="input" value={summary} onChange={(e) => setSummary(e.target.value)} required maxLength={500} /></Field>
        <Field label="Body"><textarea className="input" rows={8} value={body} onChange={(e) => setBody(e.target.value)} required /></Field>
        <Field label="Cover image" hint="JPEG, PNG or WebP. Stored in the public SeaweedFS bucket.">
          <input className="input" type="file" accept="image/jpeg,image/png,image/webp" style={{ paddingTop: 8 }} onChange={(e) => setCover(e.target.files?.[0] ?? null)} />
        </Field>
        <ErrorText error={save.error} />
      </form>
    </Modal>
  );
}
