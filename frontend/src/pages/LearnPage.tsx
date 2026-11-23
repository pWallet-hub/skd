import { useQuery } from "@tanstack/react-query";
import { get } from "../api/client";
import type { Article } from "../api/types";
import { Badge, Card, Loading } from "../components/ui";

export default function LearnPage() {
  const articles = useQuery({ queryKey: ["articles"], queryFn: () => get<Article[]>("/content/articles") });
  return (
    <Card title="Parenting guidance">
      {articles.isLoading && <Loading />}
      <div className="articles">
        {articles.data?.map((a) => (
          <article key={a.id} className="article">
            {a.cover_image_url && <img src={a.cover_image_url} alt="" />}
            <Badge value={a.category} />
            <h3>{a.title}</h3>
            <p className="muted">{a.summary}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}
