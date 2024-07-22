from typing import List

from fastapi import APIRouter, HTTPException
from openai import OpenAI
from pydantic import BaseModel

import env

router = APIRouter(prefix="/api")
api_client = OpenAI(api_key=env.OPENAI_PRIVATE_KEY)


# 열 번에 한 번 뛰어난 코드 리뷰를 하는 것보다  열번 모두 안정적인 코드 리뷰를 하는 게 중요
# 따라서 프롬프트 엔지니어링으로 코드의 다른 내용에 대해 정확하게 알지 못하는 경우, 그에 대한 언급은 피해주는 프롬프트 추가


class ReviewRequest(BaseModel):
    branch: str
    file_path: str
    code: str


class ReviewResponse(BaseModel):
    branch: str
    file_path: str
    code: str


# TODO 비동기로 최적화 하기
@router.post("/pulls", response_model=List[ReviewResponse])
def generate_pr_code_review(reviews: List[ReviewRequest]) -> List[ReviewResponse]:
    try:
        # assistant_id가 가져오기
        assistant = api_client.beta.assistants.retrieve(assistant_id=env.ASSISTANT_ID)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving assistant: {e}")

    review_results = []
    for review in reviews:
        result_code = get_review_code(review=review, assistant_id=assistant.id)

        review_results.append(ReviewResponse(branch=review.branch,
                                             file_path=review.file_path,
                                             code=result_code))

    # swagger를 통한 테스트 편의상 일단 return 하도록 놔둠.
    # 추후에 ORM을 이용해서 DB를 저장할 지 고려중
    return review_results


def get_review_code(review: ReviewRequest, assistant_id: str) -> str:
    try:
        # 매 파일마다 새로운 Thread를 생성함.
        thread = api_client.beta.threads.create()
        # 메세지 생성
        api_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=review.code
        )
        # 실행
        run = api_client.beta.threads.runs.create_and_poll(
            assistant_id=assistant_id,
            thread_id=thread.id
        )

        while run.status != "completed":
            ...

        messages = api_client.beta.threads.messages.list(
            thread_id=thread.id,
        )

        return messages.data[0].content[0].text.value

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing review for {review.file_path}: {e}")
