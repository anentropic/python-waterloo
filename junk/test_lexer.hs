{-# LANGUAGE CPP              #-}
{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE MultiWayIf       #-}
{-# LANGUAGE TupleSections    #-}
{-# LANGUAGE TypeFamilies     #-}

--module Text.Megaparsec.Char.LexerSpec (spec) where

import Control.Applicative
import Control.Monad (void)
import Data.Char hiding (ord)
import Data.List (isInfixOf)
import Data.Proxy
import Data.Maybe
import Data.Monoid ((<>))
import Data.Scientific (Scientific, fromFloatDigits)
import Data.Void (Void)
import Numeric (showInt, showHex, showOct, showFFloatAlt)
--import Test.Hspec
--import Test.Hspec.Megaparsec
--import Test.Hspec.Megaparsec.AdHoc
import Test.QuickCheck
import Text.Megaparsec
import Text.Megaparsec.Char.Lexer
import qualified Text.Megaparsec.Char as C


mkIndent :: String -> Int -> Gen String
mkIndent x n = (++) <$> mkIndent' x n <*> eol
  where
    eol = frequency [(5, return "\n"), (1, listOf1 (return '\n'))]

mkIndent' :: String -> Int -> Gen String
mkIndent' x n = concat <$> sequence [spc, sym, tra]
  where
    spc = frequency [(5, vectorOf n itm), (1, listOf itm)]
    tra = listOf itm
    itm = elements " \t"
    sym = return x

sc :: Parser ()
sc = space (void $ takeWhile1P Nothing f) empty empty
  where
    f x = x == ' ' || x == '\t'

scn :: Parser ()
scn = space C.space1 l b
  where
    l = skipLineComment "//"
    b = skipBlockComment "/*" "*/"

getIndent :: String -> Int
getIndent = length . takeWhile isSpace

getCol :: String -> Pos
getCol x = sourceColumn .
  updatePosString defaultTabWidth (initialPos "") $ take (getIndent x) x

sbla, sblb, sblc :: String
sbla = "aaa"
sblb = "bbb"
sblc = "ccc"

type Parser = Parsec Void String

-- Working with source position

-- | A helper function that is used to advance 'SourcePos' given a 'String'.

updatePosString
  :: Pos               -- ^ Tab width
  -> SourcePos         -- ^ Initial position
  -> String            -- ^ 'String' — collection of tokens to process
  -> SourcePos         -- ^ Final position
updatePosString = advanceN (Proxy :: Proxy String)



main = do
    let (l0, l1, l2, l3, l4) = (" aaa\n", "     bbb\n", "       ccc\n", "     bbb\n", "       ccc")
        (col0, col1, col2, col3, col4) =
          (getCol l0, getCol l1, getCol l2, getCol l3, getCol l4)
        fragments = [l0,l1,l2,l3,l4]
        g x = sum (length <$> take x fragments)
        s = concat fragments
        p = lvla <* eof
        lvla = indentBlock scn $ IndentMany mn      (l sbla) lvlb <$ b sbla
        lvlb = indentBlock scn $ IndentSome Nothing (l sblb) lvlc <$ b sblb
        lvlc = indentBlock scn $ IndentNone                  sblc <$ b sblc
        b    = symbol sc
        l x  = return . (x,)
        --ib'  = mkPos (fromIntegral ib)
        --ib  = fromMaybe 2 mn'
        --mn' = getSmall . getPositive <$> mn''
        --mn  = mkPos . fromIntegral <$> mn'
        mn = Just (mkPos 6)

        cols = [col0, col1, col2, col3, col4]

    -- `show` is like "to string"
    putStrLn (show cols)
    putStrLn (show fragments) 
    parseTest p s
    --if | col1 <= col0 -> prs p s `shouldFailWith`
    --     err (posN (getIndent l1 + g 1) s) (utok (head sblb) <> eeof)
    --   | isJust mn && col1 /= ib' -> prs p s `shouldFailWith`
    --     errFancy (posN (getIndent l1 + g 1) s) (ii EQ ib' col1)
    --   | col2 <= col1 -> prs p s `shouldFailWith`
    --     errFancy (posN (getIndent l2 + g 2) s) (ii GT col1 col2)
    --   | col3 == col2 -> prs p s `shouldFailWith`
    --     err (posN (getIndent l3 + g 3) s) (utoks sblb <> etoks sblc <> eeof)
    --   | col3 <= col0 -> prs p s `shouldFailWith`
    --     err (posN (getIndent l3 + g 3) s) (utok (head sblb) <> eeof)
    --   | col3 < col1 -> prs p s `shouldFailWith`
    --     errFancy (posN (getIndent l3 + g 3) s) (ii EQ col1 col3)
    --   | col3 > col1 -> prs p s `shouldFailWith`
    --     errFancy (posN (getIndent l3 + g 3) s) (ii EQ col2 col3)
    --   | col4 <= col3 -> prs p s `shouldFailWith`
    --     errFancy (posN (getIndent l4 + g 4) s) (ii GT col3 col4)
    --   | otherwise -> prs p s `shouldParse`
    --     (sbla, [(sblb, [sblc]), (sblb, [sblc])])
