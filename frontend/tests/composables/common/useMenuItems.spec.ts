import { describe, it, expect } from "vitest";
import { useMenuItems } from "../../../composables/common/useMenuItems";

describe("useMenuItems", () => {
  const mockActions = {
    navigateToRanking: () => {},
    navigateToScreenSetting: () => {},
    navigateToAiTyping: () => {},
    navigateToUserAdmin: () => {},
  };

  it("一般ユーザーの場合、管理者メニューを含まない", () => {
    const { homeMenuItems } = useMenuItems(mockActions, false);

    expect(homeMenuItems.value.length).toBe(4);
    expect(
      homeMenuItems.value.find((item: any) => item.text === "ユーザ管理")
    ).toBeUndefined();
  });

  it("管理者の場合、管理者メニューを含む", () => {
    const { homeMenuItems } = useMenuItems(mockActions, true);

    expect(homeMenuItems.value.length).toBe(5);
    expect(
      homeMenuItems.value.find((item: any) => item.text === "ユーザ管理")
    ).toBeDefined();
  });

  it("画面設定メニューが正しい項目を含む", () => {
    const { screenSettingMenuItems } = useMenuItems(mockActions, false);

    expect(screenSettingMenuItems.value.map((item: any) => item.text)).toEqual([
      "画面共通設定",
      "タイピング画面設定",
      "β：カラーカスタマイズ",
    ]);
  });

  it("getActionが正しいアクションを返す", () => {
    const { getAction } = useMenuItems(mockActions, false);

    expect(getAction("navigateToRanking")).toBe(mockActions.navigateToRanking);
    expect(getAction("nonexistentAction")).toBeUndefined();
  });
});
