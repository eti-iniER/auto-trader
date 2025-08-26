import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { images } from "@/constants/images";
import { paths } from "@/paths";
import { FiArrowRight } from "react-icons/fi";
import { Link } from "react-router";

export const PageNotFound = () => {
  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md rounded-md shadow-none">
        <CardHeader className="text-center">
          <div className="flex flex-col items-center space-y-4">
            <img
              src={images.candlestick}
              alt="AutoTrader Logo"
              className="h-16 w-16"
            />
            <div className="space-y-2">
              <CardTitle className="text-6xl font-bold text-gray-900">
                404
              </CardTitle>
              <CardDescription className="text-lg text-gray-600">
                Page not found
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2 text-center">
            <p className="text-gray-600">
              Sorry, the page you're looking for doesn't exist.
            </p>
            <p className="text-sm text-gray-500">
              The page may have been moved, deleted, or you may have entered an
              incorrect URL.
            </p>
          </div>
          <Button asChild className="w-full">
            <Link
              to={paths.authentication.LOGIN}
              className="flex items-center justify-center gap-2"
            >
              Go to login
              <FiArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
