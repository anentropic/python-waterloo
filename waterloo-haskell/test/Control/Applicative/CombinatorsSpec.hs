{-# LANGUAGE CPP        #-}
{-# LANGUAGE MultiWayIf #-}
{-# LANGUAGE ScopedTypeVariables #-}

module Control.Applicative.CombinatorsSpec (spec) where

--import Control.Applicative.Combinators
import Data.Char (isLetter, isDigit)
import Data.List (intersperse)
import Data.Maybe (fromMaybe, maybeToList, isNothing, fromJust)
import Test.Hspec
import Test.Hspec.Megaparsec
import Test.Hspec.Megaparsec.AdHoc
import Test.QuickCheck
import Text.Megaparsec
import Text.Megaparsec.Char
import Text.Megaparsec.Stream (Token)
import Text.Printf

#if !MIN_VERSION_base(4,11,0)
import Data.Monoid
#endif


spec :: Spec
spec = do

  describe "between" $
    it "works" . property $ \pre c n' post -> do
      let p = between (string pre) (string post) (many (char c))
          n = getNonNegative n'
          b = length (takeWhile (== c) post)
          z = replicate n c
          s = pre ++ z ++ post
      -- putStrLn (printf "s = %s + %s + %s" (show pre) (show z) (show post))
      if (z == post && post /= "") || (b > 0)
        then prs_ p s `shouldFailWith` err (length pre + n + b)
          ( etoks post <> etok c <>
            if length post == b
              then ueof
              else utoks (drop b post) )
        else prs_ p s `shouldParse` z

  -- "0" "0" "0" 
  -- "" "/" "/"
  describe "between v2" $
    it "works" $ do
      let p = between ppre ppost (many pc)
          pc :: Parser Char = (char c)
          ppre :: Parser String = (string pre)
          ppost :: Parser String = (string post)
          pre = ""
          post = "10"
          c = (head "0")
          n = 1
          b = 0
          z = replicate n c
          s = pre ++ z ++ post
      putStrLn (printf "s = %s + %s + %s" pre z post)
      if (z == post && post /= "") || (b > 0)
        then prs_ p s `shouldFailWith` err (length pre + n + b)
          ( etoks post <> etok c <>
            if length post == b
              then ueof
              else utoks (drop b post) )
        else prs_ p s `shouldParse` z
