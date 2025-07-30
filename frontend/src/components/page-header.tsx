interface PageHeaderProps {
  title: string;
  description?: string;
}

export const PageHeader = ({ title, description }: PageHeaderProps) => {
  return (
    <div className="mb-6 flex flex-col gap-2">
      <h1 className="text-2xl leading-none font-semibold text-neutral-900">
        {title}
      </h1>
      {description && (
        <p className="-mt-1 text-sm text-gray-600">{description}</p>
      )}
    </div>
  );
};
